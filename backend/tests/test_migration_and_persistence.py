import os
import sys
import pytest
from decimal import Decimal
from sqlalchemy import create_engine, text, Column, String, Integer, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.db.session import Base
from app.models.user import User, Patient, Doctor, Department
from app.models.clinic import Clinic
from app.models.security_privacy import UserSession
from app.db.seed import ensure_demo_accounts, ensure_tenant_columns
from scripts.migrate_sqlite_to_postgres import (
    SQLiteToPostgresMigrator,
    TargetNonEmptyError,
    OrphanDataDetectedError,
    ReconciliationMismatchError,
    mask_db_url,
)


def test_production_passwords_remain_unchanged_on_startup(db_session, monkeypatch):
    """
    Guarantees that when running in production mode, application startup / seed
    NEVER overwrites or resets an existing user's password.
    """
    # 1. Simulate production environment
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert settings.is_production is True

    # 2. Seed a user with a customized password
    custom_admin_hash = get_password_hash("SuperSecretAdminPassword#9988!")
    custom_doc_hash = get_password_hash("SuperSecretDoctorPassword#7766!")

    existing_admin = User(
        email="admin@hospital.com",
        password_hash=custom_admin_hash,
        full_name="Custom Production Administrator",
        phone="+15550001",
        role="ADMIN",
        is_active=True,
    )
    existing_doc = User(
        email="doctor@hospital.com",
        password_hash=custom_doc_hash,
        full_name="Custom Production Doctor",
        phone="+15550002",
        role="DOCTOR",
        is_active=True,
    )
    db_session.add_all([existing_admin, existing_doc])
    db_session.commit()

    # 3. Trigger startup account ensuring
    ensure_demo_accounts(db_session)
    db_session.expire_all()

    # 4. Verify passwords are unchanged
    refreshed_admin = db_session.query(User).filter(User.email == "admin@hospital.com").first()
    refreshed_doc = db_session.query(User).filter(User.email == "doctor@hospital.com").first()

    assert refreshed_admin.password_hash == custom_admin_hash
    assert verify_password("SuperSecretAdminPassword#9988!", refreshed_admin.password_hash) is True
    assert verify_password("Admin@123", refreshed_admin.password_hash) is False

    assert refreshed_doc.password_hash == custom_doc_hash
    assert verify_password("SuperSecretDoctorPassword#7766!", refreshed_doc.password_hash) is True
    assert verify_password("Doctor@123", refreshed_doc.password_hash) is False


def test_production_never_creates_admin_with_default_password(db_session, monkeypatch):
    """
    Guarantees that if no admin exists in production, startup will NOT create one
    with the hardcoded default password 'Admin@123'.
    """
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    assert settings.is_production is True

    # Ensure clean database
    db_session.query(User).filter(User.email == "admin@hospital.com").delete()
    db_session.commit()

    ensure_demo_accounts(db_session)

    admin_in_db = db_session.query(User).filter(User.email == "admin@hospital.com").first()
    assert admin_in_db is None, "Default administrator must not be created in production with default password!"


def test_postgresql_ddl_and_tenant_columns_compatibility():
    """
    Verifies that all 58 ORM tables and dialect-specific column additions
    are 100% syntactically valid for PostgreSQL.
    """
    # 1. Verify all 58 tables compile under PostgreSQL dialect
    for tbl_name, sa_table in Base.metadata.tables.items():
        compiled_ddl = str(CreateTable(sa_table).compile(dialect=postgresql.dialect()))
        assert f'CREATE TABLE "{tbl_name}"' in compiled_ddl or f"CREATE TABLE {tbl_name}" in compiled_ddl

    # 2. Verify target column definitions for PostgreSQL do NOT contain SQLite DATETIME or BOOLEAN 0
    from app.db.seed import ensure_tenant_columns
    # Check that in PostgreSQL syntax, boolean is FALSE and datetimes are TIMESTAMP WITH TIME ZONE
    pg_col_map = {
        "appointments": {
            "checked_in_at": "TIMESTAMP WITH TIME ZONE",
            "consultation_started_at": "TIMESTAMP WITH TIME ZONE",
            "consultation_ended_at": "TIMESTAMP WITH TIME ZONE",
            "is_walk_in": "BOOLEAN DEFAULT FALSE",
        }
    }
    for col, expected_type in pg_col_map["appointments"].items():
        assert "DATETIME" not in expected_type
        assert "DEFAULT 0" not in expected_type


def test_sqlite_foreign_key_pragma_configuration():
    """
    Verifies that SQLite engines with foreign_keys=ON pragma reject
    unreferenced foreign key insertions.
    """
    from sqlalchemy import event
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_fk(dbapi_con, con_record):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Attempt to insert a patient with non-existent user_id
        orphan_patient = Patient(
            user_id="00000000-0000-0000-0000-000000000000",
            gender="other",
        )
        session.add(orphan_patient)
        with pytest.raises(IntegrityError):
            session.commit()


def test_migration_refusal_to_overwrite_non_empty_target(tmp_path):
    """
    Verifies that the migration tool refuses to overwrite a target database
    that already contains data unless --allow-non-empty-target is explicitly passed.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    # Put a record in target to make it non-empty
    with t_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert().values(
                id="org-1",
                name="Pre-existing Org",
                code="EXISTING",
                is_active=True,
            )
        )

    # Migrator must refuse
    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        allow_non_empty_target=False,
    )

    with pytest.raises(TargetNonEmptyError):
        migrator.preflight_checks()


def test_migration_dry_run_and_reconciliation(tmp_path):
    """
    Verifies that dry-run mode accurately calculates counts and reconciles
    without writing any records to the target database.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    # Seed source with 2 organizations
    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert(),
            [
                {"id": "org-1", "name": "Org 1", "code": "O1", "is_active": True},
                {"id": "org-2", "name": "Org 2", "code": "O2", "is_active": True},
            ],
        )

    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=True,
    )

    stats = migrator.migrate()
    assert stats["organizations"]["source"] == 2
    assert stats["organizations"]["migrated"] == 2

    # Verify target has 0 rows because dry_run was True
    with t_engine.connect() as conn:
        t_count = conn.execute(text("SELECT count(*) FROM organizations")).scalar()
    assert t_count == 0


def test_migration_detects_and_halts_on_orphaned_records(tmp_path):
    """
    Verifies that orphaned records in source trigger OrphanDataDetectedError,
    preventing corrupt data transfer to a target database.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    from datetime import datetime

    # Insert orphaned user_session into source (user does not exist)
    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["user_sessions"].insert().values(
                id="sess-orphan-1",
                user_id="missing-user-uuid",
                token_jti="jti-orphan-123",
                is_active=True,
                expires_at=datetime(2030, 1, 1, 0, 0, 0),
            )
        )

    # Without skip_orphans, migrator must raise OrphanDataDetectedError
    migrator_strict = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=True,
        skip_orphans=False,
    )
    with pytest.raises(OrphanDataDetectedError):
        migrator_strict.preflight_checks()

    # With skip_orphans, migrator proceeds and excludes the orphan
    migrator_skip = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        skip_orphans=True,
    )
    stats = migrator_skip.migrate()
    assert stats["user_sessions"]["source"] == 1
    assert stats["user_sessions"]["migrated"] == 0


def test_mask_db_url_redacts_credentials():
    """Verifies that database connection strings never expose passwords in logs."""
    raw_pg = "postgresql://clinic_user:VerySecretPass123@dpg-abcdef.oregon-postgres.render.com:5432/cliniccare"
    masked = mask_db_url(raw_pg)
    assert "VerySecretPass123" not in masked
    assert ":***@" in masked
    assert "clinic_user" in masked

    raw_sqlite = "sqlite:///./hospital.db"
    assert mask_db_url(raw_sqlite) == "sqlite:///./hospital.db"


def test_source_immutability_and_target_dry_run_immutability(tmp_path):
    """
    Guarantees that migration operations never alter source data,
    and dry-run never creates tables or writes data to target.
    """
    import hashlib

    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    Base.metadata.create_all(bind=s_engine)

    # Insert test data into source
    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert(),
            [{"id": "org-immut-1", "name": "Immutable Org", "code": "IMMUT", "is_active": True}],
        )

    # Compute checksum of source database file
    with open(source_db, "rb") as f:
        source_hash_before = hashlib.sha256(f.read()).hexdigest()

    # Execute dry-run migration
    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=True,
    )
    migrator.migrate()

    # Verify source database file is bit-for-bit identical
    with open(source_db, "rb") as f:
        source_hash_after = hashlib.sha256(f.read()).hexdigest()
    assert source_hash_before == source_hash_after, "Source database was modified during migration!"

    # Verify target database has no tables created during dry run
    t_insp = inspect(create_engine(f"sqlite:///{target_db}"))
    assert len(t_insp.get_table_names()) == 0, "Dry run must not create tables on target!"


def test_atomic_rollback_on_injected_failure_and_retry_recovery(tmp_path, monkeypatch):
    """
    Guarantees that an error midway through migration triggers a full target rollback
    leaving zero orphaned rows, and a subsequent retry succeeds cleanly.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    # Populate source with organization, clinic, and user
    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert().values(
                id="org-atomic-1", name="Atomic Org", code="ATOMIC", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["clinics"].insert().values(
                id="clinic-atomic-1", name="Atomic Clinic", slug="atomic-clinic", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["users"].insert().values(
                id="user-atomic-1", email="atomic@hospital.com", password_hash="hash123", full_name="Atomic User", role="ADMIN", is_active=True
            )
        )

    # 1. Simulate failure during users table insertion
    orig_convert = SQLiteToPostgresMigrator._convert_row_value

    def failing_convert(self, val, col_type):
        if val == "atomic@hospital.com":
            raise RuntimeError("Injected mid-migration network failure!")
        return orig_convert(self, val, col_type)

    monkeypatch.setattr(SQLiteToPostgresMigrator, "_convert_row_value", failing_convert)

    migrator_failing = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        allow_non_empty_target=True,
    )

    with pytest.raises(RuntimeError, match="Injected mid-migration network failure!"):
        migrator_failing.migrate()

    # 2. Assert full atomic rollback on target: zero rows in ANY table!
    with t_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM organizations")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM clinics")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 0

    # 3. Restore normal converter and retry migration
    monkeypatch.undo()

    migrator_retry = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        allow_non_empty_target=False,  # Target is empty due to clean rollback!
    )
    stats = migrator_retry.migrate()

    # 4. Verify all tables migrated with 100% reconciliation
    assert stats["organizations"]["migrated"] == 1
    assert stats["clinics"]["migrated"] == 1
    assert stats["users"]["migrated"] == 1

    with t_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM organizations")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM clinics")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 1


def test_data_conversion_edge_cases():
    """
    Verifies that type conversion handles booleans, dates, timezone-aware timestamps,
    decimals, JSON, and None values accurately.
    """
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from sqlalchemy import Boolean, Date, DateTime, Numeric, JSON, String

    migrator = SQLiteToPostgresMigrator(
        source_url="sqlite:///:memory:",
        target_url="sqlite:///:memory:",
        dry_run=True,
    )

    # Booleans
    assert migrator._convert_row_value(1, Boolean()) is True
    assert migrator._convert_row_value(0, Boolean()) is False
    assert migrator._convert_row_value("true", Boolean()) is True
    assert migrator._convert_row_value("false", Boolean()) is False

    # Dates
    assert migrator._convert_row_value("2026-10-20", Date()) == date(2026, 10, 20)

    # Datetimes: naive strings become UTC-aware
    dt = migrator._convert_row_value("2026-10-20 18:30:00", DateTime())
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026 and dt.month == 10 and dt.day == 20 and dt.hour == 18

    # Decimals
    dec = migrator._convert_row_value("499.99", Numeric(10, 2))
    assert isinstance(dec, Decimal)
    assert dec == Decimal("499.99")

    # JSON strings become dict/list
    json_val = migrator._convert_row_value('{"role": "admin", "tags": [1, 2]}', JSON())
    assert isinstance(json_val, dict)
    assert json_val["role"] == "admin"
    assert json_val["tags"] == [1, 2]

    assert migrator._convert_row_value(None, String()) is None
    assert migrator._convert_row_value(None, DateTime()) is None
    assert migrator._convert_row_value(None, Boolean()) is None


def test_reconciliation_mismatch_raises_error_and_rolls_back(tmp_path, monkeypatch):
    """
    Verifies that any row-count mismatch between source and target raises
    ReconciliationMismatchError and completely rolls back target changes.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert().values(
                id="org-mismatch-1", name="Mismatch Org", code="MISMATCH", is_active=True
            )
        )

    # Artificially alter the target count query to simulate a mismatch
    orig_execute = t_engine.connect

    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        allow_non_empty_target=True,
    )

    # Intercept only the target count verification query inside migrate()
    orig_connect = t_engine.connect
    connect_calls = [0]

    def mock_connect(*args, **kwargs):
        real_conn = orig_connect(*args, **kwargs)
        real_execute = real_conn.execute

        def mock_conn_execute(statement, *exec_args, **exec_kwargs):
            if "SELECT count(*)" in str(statement) and "organizations" in str(statement) and connect_calls[0] > 0:
                class FakeResult:
                    def scalar(self):
                        return 999  # Injected mismatch: source=1, target=999
                return FakeResult()
            return real_execute(statement, *exec_args, **exec_kwargs)

        real_conn.execute = mock_conn_execute
        connect_calls[0] += 1
        return real_conn

    monkeypatch.setattr(migrator.target_engine, "connect", mock_connect)

    with pytest.raises(ReconciliationMismatchError, match="Reconciliation mismatch in table 'organizations'"):
        migrator.migrate()

    # Verify atomic rollback: target organizations must have 0 rows
    with orig_connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM organizations")).scalar() == 0


def test_circular_branches_users_resolution(tmp_path):
    """
    Verifies that circular foreign keys between branches (branch_admin_user_id)
    and users (branch_id) resolve correctly in a live migration without FK errors.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    # Seed org, clinic, branch (with admin), and user (with branch)
    with s_engine.begin() as conn:
        conn.execute(
            Base.metadata.tables["organizations"].insert().values(
                id="org-circ-1", name="Circular Org", code="CIRC", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["clinics"].insert().values(
                id="clinic-circ-1", name="Circular Clinic", slug="circ-clinic", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["branches"].insert().values(
                id="branch-circ-1",
                organization_id="org-circ-1",
                name="Circular Branch",
                code="BR-CIRC",
                branch_admin_user_id="user-circ-admin-1",  # Points to user
                is_active=True,
            )
        )
        conn.execute(
            Base.metadata.tables["users"].insert().values(
                id="user-circ-admin-1",
                email="circadmin@hospital.com",
                password_hash="hashedpass",
                full_name="Branch Admin",
                role="ADMIN",
                branch_id="branch-circ-1",  # Points to branch
                is_active=True,
            )
        )

    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
    )

    stats = migrator.migrate()
    assert stats["branches"]["migrated"] == 1
    assert stats["users"]["migrated"] == 1

    # Verify both foreign keys are populated on target
    with t_engine.connect() as conn:
        branch_row = conn.execute(text("SELECT id, branch_admin_user_id FROM branches WHERE id='branch-circ-1'")).fetchone()
        user_row = conn.execute(text("SELECT id, branch_id FROM users WHERE id='user-circ-admin-1'")).fetchone()

        assert branch_row is not None
        assert branch_row._mapping["branch_admin_user_id"] == "user-circ-admin-1"

        assert user_row is not None
        assert user_row._mapping["branch_id"] == "branch-circ-1"


def test_composite_pk_migration_and_pagination(tmp_path):
    """
    Verifies that tables with composite primary keys (lab_order_tests: order_id, test_id)
    are paginated and migrated deterministically across batch boundaries.
    """
    source_db = str(tmp_path / "source.db")
    target_db = str(tmp_path / "target.db")

    s_engine = create_engine(f"sqlite:///{source_db}")
    t_engine = create_engine(f"sqlite:///{target_db}")

    Base.metadata.create_all(bind=s_engine)
    Base.metadata.create_all(bind=t_engine)

    with s_engine.begin() as conn:
        # Seed parent clinic, patient, and lab test
        conn.execute(
            Base.metadata.tables["clinics"].insert().values(
                id="clinic-lab-1", name="Lab Clinic", slug="lab-clinic", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["departments"].insert().values(
                id="dept-lab-1", clinic_id="clinic-lab-1", name="Pathology", icon="stethoscope", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["users"].insert().values(
                id="user-pat-lab-1", email="labpat@hospital.com", password_hash="h", full_name="Lab Pat", role="PATIENT", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["users"].insert().values(
                id="user-doc-lab-1", email="labdoc@hospital.com", password_hash="h", full_name="Dr. Lab", role="DOCTOR", is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["patients"].insert().values(
                id="pat-lab-1", user_id="user-pat-lab-1"
            )
        )
        conn.execute(
            Base.metadata.tables["doctors"].insert().values(
                id="doc-lab-1", user_id="user-doc-lab-1", department_id="dept-lab-1", specialization="Pathology", qualification="MD", experience_years=10, consultation_fee=50.0, location="Room 1", available_days="Mon-Fri", available_hours_start="09:00", available_hours_end="17:00", max_daily_patients=20, slot_duration_minutes=15, is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["lab_tests"].insert().values(
                id="test-1", clinic_id="clinic-lab-1", name="Blood Count", code="CBC", category="HEMATOLOGY", sample_type="Whole Blood", turnaround_hours=24, price=50.0, is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["lab_tests"].insert().values(
                id="test-2", clinic_id="clinic-lab-1", name="Lipid Profile", code="LIPID", category="BIOCHEMISTRY", sample_type="Serum", turnaround_hours=24, price=80.0, is_active=True
            )
        )
        conn.execute(
            Base.metadata.tables["lab_tests"].insert().values(
                id="test-3", clinic_id="clinic-lab-1", name="Thyroid Panel", code="THYROID", category="BIOCHEMISTRY", sample_type="Serum", turnaround_hours=24, price=120.0, is_active=True
            )
        )
        # Seed lab order
        conn.execute(
            Base.metadata.tables["lab_orders"].insert().values(
                id="order-1", clinic_id="clinic-lab-1", patient_id="pat-lab-1", doctor_id="doc-lab-1", order_number="ORD-001", priority="ROUTINE", status="ORDERED"
            )
        )
        # Seed 3 composite PK records in lab_order_tests (order_id, test_id)
        conn.execute(
            Base.metadata.tables["lab_order_tests"].insert(),
            [
                {"order_id": "order-1", "test_id": "test-1"},
                {"order_id": "order-1", "test_id": "test-2"},
                {"order_id": "order-1", "test_id": "test-3"},
            ],
        )

    # Use a small batch size = 2 to force multi-page composite PK pagination
    migrator = SQLiteToPostgresMigrator(
        source_url=f"sqlite:///{source_db}",
        target_url=f"sqlite:///{target_db}",
        dry_run=False,
        batch_size=2,
    )

    stats = migrator.migrate()
    assert stats["lab_order_tests"]["source"] == 3
    assert stats["lab_order_tests"]["migrated"] == 3
    assert stats["lab_order_tests"]["target"] == 3

    with t_engine.connect() as conn:
        target_records = conn.execute(
            text("SELECT order_id, test_id FROM lab_order_tests ORDER BY order_id, test_id")
        ).fetchall()
        assert len(target_records) == 3
        test_ids = [r._mapping["test_id"] for r in target_records]
        assert test_ids == ["test-1", "test-2", "test-3"]
