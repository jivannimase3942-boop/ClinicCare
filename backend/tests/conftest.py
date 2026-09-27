import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app
from app.core.security import get_password_hash
from app.models.user import User, Patient, Doctor, Department


# Use in-memory SQLite database with StaticPool for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    # Department
    dept = Department(name="Cardiology", description="Heart Clinic", icon="Heart", is_active=True)
    db_session.add(dept)
    db_session.flush()

    # Admin User
    admin = User(
        email="admin@hospital.com",
        password_hash=get_password_hash("Admin@123"),
        full_name="Admin User",
        role="ADMIN",
        is_active=True,
    )
    db_session.add(admin)

    # Doctor User & Doctor
    doc_user = User(
        email="doctor@hospital.com",
        password_hash=get_password_hash("Doctor@123"),
        full_name="Dr. Test Specialist",
        role="DOCTOR",
        is_active=True,
    )
    db_session.add(doc_user)
    db_session.flush()

    doctor = Doctor(
        user_id=doc_user.id,
        department_id=dept.id,
        specialization="Cardiologist",
        qualification="MD",
        experience_years=10,
        consultation_fee=100.0,
        location="Room 101",
        available_days="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday",
        available_hours_start="09:00",
        available_hours_end="17:00",
        is_active=True,
    )
    db_session.add(doctor)

    # Patient User & Patient
    pat_user = User(
        email="patient@hospital.com",
        password_hash=get_password_hash("Patient@123"),
        full_name="John Patient",
        phone="+1555123456",
        role="PATIENT",
        is_active=True,
    )
    db_session.add(pat_user)
    db_session.flush()

    patient = Patient(
        user_id=pat_user.id,
        gender="male",
        blood_group="O+",
    )
    db_session.add(patient)
    db_session.commit()

    # Ambulance
    from app.models.ambulance import Ambulance
    amb = Ambulance(
        vehicle_number="AMB-001",
        model="Sprinter BLS",
        ambulance_type="Basic Life Support (BLS)",
        status="available",
        base_station="Main Campus",
        current_location="Emergency Bay",
        is_active=True,
    )
    db_session.add(amb)

    # Blood Bank & Inventory
    from app.models.blood import BloodBank, BloodInventory
    bb = BloodBank(
        name="ClinicCare Central Blood Bank",
        city="Metropolis",
        address="100 Medical Blvd",
        phone="+15550000",
        is_verified=True,
    )
    db_session.add(bb)
    db_session.flush()

    inv1 = BloodInventory(blood_bank_id=bb.id, blood_group="O+", units_available=15, status="available")
    inv2 = BloodInventory(blood_bank_id=bb.id, blood_group="A+", units_available=8, status="available")
    db_session.add_all([inv1, inv2])

    # Facility
    from app.models.facility import Facility
    fac = Facility(
        name="ClinicCare Multispeciality Hospital",
        facility_type="Multispeciality Hospital",
        services="Cardiology, Neurology, Pediatrics",
        address="100 Hospital Drive",
        city="Metropolis",
        phone="+15550100",
        emergency_hotline="911",
        is_emergency_ready=True,
        is_active=True,
    )
    db_session.add(fac)
    db_session.commit()



    return {
        "dept": dept,
        "admin": admin,
        "doctor": doctor,
        "patient": patient,
        "patient_user": pat_user,
    }

