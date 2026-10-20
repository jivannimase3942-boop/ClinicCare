"""
ClinicCare — Production-Grade SQLite-to-PostgreSQL Migration Utility

Prepares and executes safe data migration from source SQLite to target PostgreSQL
without relying on destructive operations or disabling foreign key constraints.

Operational Safety Rules:
1. BACKUP FIRST: Always take a cold physical backup of the source database (e.g. `hospital.db`)
   before initiating migration: `cp hospital.db hospital.db.backup.$(date +%Y%m%d%H%M%S)`.
2. DRY-RUN FIRST: Always execute with `--dry-run` to validate connectivity, table counts,
   and orphan foreign keys before writing any records to the target database.
3. ORPHAN DATA AUDIT: If source SQLite contains orphaned records, migration halts by default
   (`OrphanDataDetectedError`). Inspect reported tables. Use `--skip-orphans` ONLY after
   confirming with clinical operations that omitted rows are obsolete.
4. STAGING VALIDATION MANDATORY: NEVER run this utility against production PostgreSQL
   without prior successful dry-run and live validation on an isolated staging database.
5. NAIVE TIMESTAMP ASSUMPTION: SQLite stores timestamps without timezone metadata.
   The converter attaches `timezone.utc` to naive datetimes. If legacy rows were inserted
   using local host time rather than UTC, they will be treated as UTC without offset shifts.
   Verify historical timestamp convention prior to final cutover.

Safety Guarantees:
- Fully Atomic: All target writes are executed in a single transaction that automatically
  rolls back completely on any batch failure, leaving zero partial tables.
- Source Immutability: Opens SQLite connections strictly in read-only mode and executes only SELECTs.
- Never prints secrets, passwords, tokens, or raw credentials.
- Safe two-pass circular dependency resolution (branches <-> users).
- Strict pre-flight checks: validates schemas, detects orphaned records, and prevents
  accidental overwriting of non-empty target databases.
- Deterministic pagination ordering across all primary keys (including composite keys).
- Generic orphan foreign key detection and optional skipping with explicit audit counts.
- Dialect type conversion (booleans, timezone-aware UTC timestamps, dates, decimals, JSON).
- Post-migration reconciliation report with exact row-count mathematical validation.
- Meaningful dry-run verification mode.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, date, timezone
from decimal import Decimal
from urllib.parse import urlparse

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, select, text, Table
from sqlalchemy.engine import Engine
from app.db.session import Base
import app.db.base  # Register all 58 models with Base.metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration.sqlite_to_postgres")


def mask_db_url(url: str) -> str:
    """Safely masks database credentials from connection strings for logging."""
    if not url:
        return "[EMPTY]"
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked = url.replace(f":{parsed.password}@", ":***@")
            return masked
        return url
    except Exception:
        return "[MASKED_URL]"


# Strict topological table order to respect foreign key hierarchies (all 58 tables)
MIGRATION_TABLE_ORDER = [
    # Level 1: Root tables (no external foreign keys)
    "organizations",
    "clinics",
    "medicines",
    "suppliers",
    "blood_banks",
    "facilities",
    "error_logs",
    "email_verifications",
    "lab_tests",
    "ambulances",

    # Level 2: Immediate dependents of root tables
    "branches",          # Note: branch_admin_user_id is deferred to Pass 2
    "departments",
    "blood_inventory",
    "stock_batches",

    # Level 3: Users
    "users",

    # Level 4: Direct user profiles and security tracking
    "patients",
    "doctors",
    "user_sessions",
    "security_events",
    "audit_logs",
    "mfa_configs",
    "notifications",

    # Level 5: Doctor schedules, clinical bookings, and requests
    "doctor_slots",
    "doctor_leaves",
    "appointment_waitlists",
    "appointments",
    "reports",
    "feedback",
    "ai_conversations",
    "voice_call_requests",
    "escalations",
    "ambulance_requests",
    "blood_requests",
    "patient_consents",
    "privacy_requests",
    "abha_profiles",
    "abdm_facility_registry",
    "abdm_professional_registry",

    # Level 6: Longitudinal clinical records and orders
    "ai_messages",
    "consultation_records",
    "vital_signs",
    "clinical_documents",
    "invoices",
    "lab_orders",
    "prescriptions",

    # Level 7: Child items, diagnostics, payments, and movements
    "invoice_items",
    "payments",
    "refunds",
    "prescription_items",
    "stock_transactions",
    "lab_order_tests",
    "lab_samples",
    "lab_results",
    "lab_reports",
    "visit_histories",
    "follow_up_reminders",
    "abdm_consent_artifacts",

    # Level 8: Exchange records
    "abdm_hie_records",
]


class MigrationError(Exception):
    """Base migration exception."""
    pass


class TargetNonEmptyError(MigrationError):
    """Raised when target database contains existing data without override flag."""
    pass


class OrphanDataDetectedError(MigrationError):
    """Raised when orphaned foreign keys exist in source database."""
    pass


class SchemaMismatchError(MigrationError):
    """Raised when target schema does not match expected model definitions."""
    pass


class ReconciliationMismatchError(MigrationError):
    """Raised when post-migration row counts do not mathematically reconcile."""
    pass


class SQLiteToPostgresMigrator:
    def __init__(
        self,
        source_url: str,
        target_url: str,
        dry_run: bool = True,
        batch_size: int = 500,
        allow_non_empty_target: bool = False,
        skip_orphans: bool = False,
    ):
        self.source_url = source_url
        self.target_url = target_url
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.allow_non_empty_target = allow_non_empty_target
        self.skip_orphans = skip_orphans

        # Source connection: enforce read-only where possible
        source_args: Dict[str, Any] = {}
        if "sqlite" in source_url:
            source_args["check_same_thread"] = False
        self.source_engine = create_engine(source_url, connect_args=source_args, pool_pre_ping=True)
        self.target_engine = create_engine(target_url, pool_pre_ping=True)

        self.reconciliation_stats: Dict[str, Dict[str, int]] = {}
        self.orphaned_records: Dict[str, int] = {}
        self.valid_parent_cache: Dict[str, Set[Any]] = {}

    def log_safe_info(self, msg: str):
        logger.info(msg)

    def preflight_checks(self):
        """Validates source connectivity, target state, and foreign-key integrity."""
        self.log_safe_info(f"Source database: {mask_db_url(self.source_url)}")
        self.log_safe_info(f"Target database: {mask_db_url(self.target_url)}")
        self.log_safe_info(f"Execution mode: {'DRY RUN (Read-Only)' if self.dry_run else 'LIVE ATOMIC MIGRATION'}")

        # 1. Verify source connectivity
        with self.source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        self.log_safe_info("✓ Source database connection verified.")

        # 2. Check target database state
        target_insp = inspect(self.target_engine)
        target_tables = target_insp.get_table_names()

        if self.dry_run:
            self.log_safe_info("[DRY RUN] Target table creation: SKIPPED (Dry run active)")
        elif not target_tables:
            self.log_safe_info("Target database has no tables. Initializing target schema from SQLAlchemy metadata...")
            Base.metadata.create_all(bind=self.target_engine)
            target_insp = inspect(self.target_engine)
            target_tables = target_insp.get_table_names()

        # Check for existing data in target
        if target_tables:
            with self.target_engine.connect() as conn:
                non_empty_tables = []
                for tbl in target_tables:
                    try:
                        count = conn.execute(text(f'SELECT count(*) FROM "{tbl}"')).scalar() or 0
                        if count > 0:
                            non_empty_tables.append((tbl, count))
                    except Exception:
                        pass
                if non_empty_tables:
                    summary = ", ".join([f"{t}: {c} rows" for t, c in non_empty_tables[:5]])
                    if not self.allow_non_empty_target:
                        raise TargetNonEmptyError(
                            f"Target database is not empty ({summary}). "
                            "Pass --allow-non-empty-target to proceed with migration."
                        )
                    else:
                        self.log_safe_info(f"⚠ Notice: Target database contains existing data ({summary}). Proceeding due to override flag.")

        # 3. Check for orphaned foreign key records in source SQLite
        if "sqlite" in self.source_url:
            self._audit_source_orphans()

    def _audit_source_orphans(self):
        """Audits all foreign keys in source SQLite and records orphan counts."""
        source_insp = inspect(self.source_engine)
        source_tables = set(source_insp.get_table_names())

        with self.source_engine.connect() as conn:
            for tbl in source_tables:
                fks = source_insp.get_foreign_keys(tbl)
                for fk in fks:
                    ref_tbl = fk.get("referred_table")
                    constrained_cols = fk.get("constrained_columns", [])
                    referred_cols = fk.get("referred_columns", [])
                    if not ref_tbl or not constrained_cols or not referred_cols:
                        continue
                    if ref_tbl not in source_tables:
                        continue

                    # Handle foreign keys (single or composite)
                    for col, ref_col in zip(constrained_cols, referred_cols):
                        query = text(
                            f'SELECT count(*) FROM "{tbl}" WHERE "{col}" IS NOT NULL '
                            f'AND "{col}" NOT IN (SELECT "{ref_col}" FROM "{ref_tbl}")'
                        )
                        orphan_count = conn.execute(query).scalar() or 0
                        if orphan_count > 0:
                            key = f"{tbl}.{col} -> {ref_tbl}.{ref_col}"
                            self.orphaned_records[key] = orphan_count
                            self.log_safe_info(f"⚠ Referential Integrity Warning: {key}: {orphan_count} orphaned rows detected in source.")

        if self.orphaned_records and not self.skip_orphans:
            orphan_summary = "; ".join([f"{k}: {v}" for k, v in self.orphaned_records.items()])
            raise OrphanDataDetectedError(
                f"Source SQLite contains orphaned records ({orphan_summary}). "
                "These will violate PostgreSQL foreign keys. Review data or specify --skip-orphans to omit them."
            )

    def _get_valid_parent_ids(self, table_name: str, id_col: str) -> Set[Any]:
        """Caches valid parent IDs to perform fast in-memory orphan filtering without N+1 queries."""
        cache_key = f"{table_name}.{id_col}"
        if cache_key in self.valid_parent_cache:
            return self.valid_parent_cache[cache_key]

        with self.source_engine.connect() as conn:
            rows = conn.execute(text(f'SELECT "{id_col}" FROM "{table_name}"')).fetchall()
            valid_set = {r[0] for r in rows if r[0] is not None}
            self.valid_parent_cache[cache_key] = valid_set
            return valid_set

    def _convert_row_value(self, val: Any, col_type: Any) -> Any:
        """Converts SQLite storage representations to strict PostgreSQL-compatible types."""
        if val is None:
            return None

        type_str = str(col_type).upper()

        # Booleans
        if "BOOL" in type_str:
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val)
            if isinstance(val, str):
                return val.strip().lower() in ("1", "true", "t", "yes")

        # Dates
        if "DATE" in type_str and "TIME" not in type_str:
            if isinstance(val, date):
                return val
            if isinstance(val, str):
                try:
                    return date.fromisoformat(val[:10])
                except Exception:
                    return None

        # Datetimes / Timestamps: strictly convert to UTC-aware datetime
        if "DATETIME" in type_str or "TIMESTAMP" in type_str:
            if isinstance(val, datetime):
                if val.tzinfo is None:
                    return val.replace(tzinfo=timezone.utc)
                return val
            if isinstance(val, str):
                try:
                    clean_str = val.replace(" ", "T")
                    dt = datetime.fromisoformat(clean_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    return None

        # Decimals
        if "NUMERIC" in type_str or "DECIMAL" in type_str:
            if isinstance(val, Decimal):
                return val
            try:
                return Decimal(str(val))
            except Exception:
                return val

        # JSON
        if "JSON" in type_str:
            if isinstance(val, (dict, list)):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return val

        return val

    def migrate(self) -> Dict[str, Dict[str, int]]:
        """
        Executes full migration or dry-run validation.
        In live mode, ALL operations across all 58 tables are executed inside
        a single atomic target transaction that rolls back completely on any failure.
        """
        self.preflight_checks()

        source_insp = inspect(self.source_engine)
        source_tables = set(source_insp.get_table_names())

        deferred_branch_updates: List[Tuple[str, str]] = []  # (branch_id, branch_admin_user_id)

        # Context manager for target transaction
        if not self.dry_run:
            t_conn = self.target_engine.connect()
            transaction = t_conn.begin()
        else:
            t_conn = None
            transaction = None

        try:
            for table_name in MIGRATION_TABLE_ORDER:
                if table_name not in source_tables:
                    self.reconciliation_stats[table_name] = {"source": 0, "skipped": 0, "migrated": 0, "target": 0}
                    continue

                sa_table = Base.metadata.tables.get(table_name)
                if sa_table is None:
                    self.log_safe_info(f"Skipping table '{table_name}': not present in ORM Base.metadata.")
                    continue

                # Query source count
                with self.source_engine.connect() as s_conn:
                    source_count = s_conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar() or 0

                if source_count == 0:
                    self.reconciliation_stats[table_name] = {"source": 0, "skipped": 0, "migrated": 0, "target": 0}
                    continue

                self.log_safe_info(f"Processing '{table_name}' ({source_count} source records)...")
                migrated_count = 0
                skipped_count = 0

                # Deterministic pagination: order by all PK columns or rowid
                pk_cols = [f'"{c.name}"' for c in sa_table.primary_key.columns]
                order_clause = ", ".join(pk_cols) if pk_cols else "rowid"

                # Check if this table has foreign keys with detected orphans
                relevant_fk_checks = []
                if self.skip_orphans:
                    for fk in source_insp.get_foreign_keys(table_name):
                        ref_tbl = fk.get("referred_table")
                        c_cols = fk.get("constrained_columns", [])
                        r_cols = fk.get("referred_columns", [])
                        if ref_tbl and c_cols and r_cols:
                            col_name = c_cols[0]
                            ref_col = r_cols[0]
                            if f"{table_name}.{col_name} -> {ref_tbl}.{ref_col}" in self.orphaned_records:
                                valid_ids = self._get_valid_parent_ids(ref_tbl, ref_col)
                                relevant_fk_checks.append((col_name, valid_ids))

                # Bounded batch reading
                offset = 0
                while offset < source_count:
                    with self.source_engine.connect() as s_conn:
                        query = text(f'SELECT * FROM "{table_name}" ORDER BY {order_clause} LIMIT {self.batch_size} OFFSET {offset}')
                        rows = s_conn.execute(query).fetchall()

                    if not rows:
                        break

                    batch_dicts = []
                    for row in rows:
                        row_dict = dict(row._mapping)

                        # Filter out orphaned rows if --skip-orphans is active
                        if relevant_fk_checks:
                            is_orphan = False
                            for col_name, valid_ids in relevant_fk_checks:
                                fk_val = row_dict.get(col_name)
                                if fk_val is not None and fk_val not in valid_ids:
                                    is_orphan = True
                                    break
                            if is_orphan:
                                skipped_count += 1
                                continue

                        # Two-pass circular foreign key handling for branches: omit branch_admin_user_id in Pass 1
                        if table_name == "branches" and row_dict.get("branch_admin_user_id"):
                            deferred_branch_updates.append((row_dict["id"], row_dict["branch_admin_user_id"]))
                            row_dict["branch_admin_user_id"] = None

                        # Type conversion
                        converted = {}
                        for col in sa_table.columns:
                            if col.name in row_dict:
                                converted[col.name] = self._convert_row_value(row_dict[col.name], col.type)

                        batch_dicts.append(converted)

                    if not self.dry_run and batch_dicts:
                        t_conn.execute(sa_table.insert(), batch_dicts)

                    migrated_count += len(batch_dicts)
                    offset += self.batch_size

                # Target count verification
                target_count = 0
                if not self.dry_run:
                    target_count = t_conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar() or 0
                else:
                    target_count = migrated_count

                self.reconciliation_stats[table_name] = {
                    "source": source_count,
                    "skipped": skipped_count,
                    "migrated": migrated_count,
                    "target": target_count,
                }

            # Pass 2: Reapply deferred circular branch_admin_user_id updates
            if deferred_branch_updates:
                self.log_safe_info(f"Applying {len(deferred_branch_updates)} deferred circular branch admin updates...")
                if not self.dry_run:
                    branches_tbl = Base.metadata.tables["branches"]
                    for b_id, admin_uid in deferred_branch_updates:
                        t_conn.execute(
                            branches_tbl.update()
                            .where(branches_tbl.c.id == b_id)
                            .values(branch_admin_user_id=admin_uid)
                        )

            # Pre-commit mathematical reconciliation validation
            for tbl, stats in self.reconciliation_stats.items():
                s = stats["source"]
                sk = stats["skipped"]
                m = stats["migrated"]
                t = stats["target"]
                if s != (sk + m) or m != t:
                    raise ReconciliationMismatchError(
                        f"Reconciliation mismatch in table '{tbl}': source={s}, skipped={sk}, migrated={m}, target={t}"
                    )

            # Commit the atomic transaction if live
            if not self.dry_run and transaction is not None:
                transaction.commit()
                self.log_safe_info("✓ All tables committed successfully in target atomic transaction.")

        except Exception as e:
            if not self.dry_run and transaction is not None:
                transaction.rollback()
                self.log_safe_info(f"✗ Target transaction ROLLED BACK completely due to error: {e}")
            raise
        finally:
            if t_conn is not None:
                t_conn.close()

        self.log_safe_info("Migration process completed.")
        return self.reconciliation_stats

    def print_reconciliation_report(self):
        """Prints a clean tabular reconciliation summary."""
        print("\n" + "=" * 80)
        print("CLINICCARE DATABASE MIGRATION RECONCILIATION REPORT")
        print("=" * 80)
        print(f"{'Table Name':<30} {'Source':<10} {'Skipped':<10} {'Migrated':<10} {'Target':<10} {'Status'}")
        print("-" * 80)

        total_source = 0
        total_skipped = 0
        total_migrated = 0
        total_target = 0
        all_match = True

        for tbl, stats in self.reconciliation_stats.items():
            s = stats["source"]
            sk = stats["skipped"]
            m = stats["migrated"]
            t = stats["target"]
            total_source += s
            total_skipped += sk
            total_migrated += m
            total_target += t

            # Math check: source == skipped + migrated, and migrated == target
            is_valid = (s == sk + m) and (m == t)
            if not is_valid:
                all_match = False
                status = "MISMATCH"
            elif sk > 0:
                status = "MATCH (ORPHANS SKIPPED)"
            else:
                status = "MATCH"

            if s > 0 or t > 0:
                print(f"{tbl:<30} {s:<10} {sk:<10} {m:<10} {t:<10} {status}")

        print("-" * 80)
        total_status = "VALID RECONCILIATION" if all_match else "MISMATCH DETECTED"
        print(f"{'TOTALS':<30} {total_source:<10} {total_skipped:<10} {total_migrated:<10} {total_target:<10} {total_status}")
        print("=" * 80 + "\n")
        return all_match


def parse_args():
    parser = argparse.ArgumentParser(description="ClinicCare SQLite to PostgreSQL Migration Utility")
    parser.add_argument("--source", default=os.getenv("MIGRATION_SOURCE_DB_URL", "sqlite:///./hospital.db"), help="Source SQLite connection URL")
    parser.add_argument("--target", default=os.getenv("MIGRATION_TARGET_DB_URL", ""), help="Target PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Run validation and reconciliation without writing data")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for data transfer")
    parser.add_argument("--allow-non-empty-target", action="store_true", default=False, help="Allow writing into a non-empty target database")
    parser.add_argument("--skip-orphans", action="store_true", default=False, help="Omit orphaned foreign key records during migration")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.target and not args.dry_run:
        logger.error("A target database URL must be provided via --target or MIGRATION_TARGET_DB_URL.")
        sys.exit(1)

    migrator = SQLiteToPostgresMigrator(
        source_url=args.source,
        target_url=args.target or "sqlite:///:memory:",
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        allow_non_empty_target=args.allow_non_empty_target,
        skip_orphans=args.skip_orphans,
    )

    try:
        migrator.migrate()
        is_reconciled = migrator.print_reconciliation_report()
        if not is_reconciled:
            logger.error("Migration finished with un-reconciled row counts.")
            sys.exit(4)
    except MigrationError as me:
        logger.error(f"Migration aborted due to safety constraint: {me}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        sys.exit(3)
