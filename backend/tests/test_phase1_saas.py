import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.clinic import Clinic
from app.models.audit import AuditLog
from app.models.user import User, Patient, Doctor
from app.models.appointment import Appointment
from app.core.roles import Role, get_permissions_for_role, has_permission
from app.services.audit_service import audit_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_role_architecture_and_permissions():
    """Verify role architecture and permission matrix."""
    # Test Super Admin has wildcard
    assert has_permission(Role.SUPER_ADMIN, "anything") is True
    assert has_permission(Role.SUPER_ADMIN, "manage_clinic") is True

    # Test Admin permissions
    admin_perms = get_permissions_for_role(Role.ADMIN)
    assert "view_audit_logs" in admin_perms
    assert "manage_clinic" in admin_perms
    assert has_permission(Role.ADMIN, "view_audit_logs") is True
    assert has_permission(Role.ADMIN, "nonexistent_perm") is False

    # Test Front Desk cannot view audit logs
    assert has_permission(Role.FRONT_DESK, "view_audit_logs") is False
    assert has_permission(Role.FRONT_DESK, "book_appointments") is True

    # Test Doctor permissions
    assert has_permission(Role.DOCTOR, "view_assigned_appointments") is True
    assert has_permission(Role.DOCTOR, "view_audit_logs") is False

    # Test Future roles exist and have appropriate permissions
    for future_role in [Role.NURSE, Role.PHARMACIST, Role.LAB_TECHNICIAN, Role.RADIOLOGIST, Role.ACCOUNTANT, Role.AMBULANCE_COORDINATOR]:
        perms = get_permissions_for_role(future_role)
        assert len(perms) > 0, f"Future role {future_role} should have configured permissions"


def test_clinic_onboarding_workflow(client, db_session):
    """Test full clinic onboarding flow with admin and department creation."""
    timestamp = int(time.time())
    onboard_payload = {
        "name": f"Sunrise Wellness Clinic {timestamp}",
        "slug": f"sunrise-clinic-{timestamp}",
        "phone": "+91 98765 43210",
        "email": f"info-{timestamp}@sunriseclinic.in",
        "address": "45 Green Glen Layout, Bellandur",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560103",
        "country": "India",
        "operating_hours": "08:30 AM - 08:30 PM (Mon-Sat)",
        "consultation_fee_default": 600.00,
        "departments": ["General Medicine", "Pediatrics", "Dermatology"],
        "services": ["OPD Consultation", "Vaccination", "Minor Procedures"],
        "admin_name": f"Dr. Ramesh Rao {timestamp}",
        "admin_email": f"admin_{timestamp}@sunriseclinic.in",
        "admin_password": "SecureAdmin@123",
        "admin_phone": "+91 98765 43211",
        "doctor_name": f"Dr. Sneha Rao {timestamp}",
        "doctor_email": f"sneha_{timestamp}@sunriseclinic.in",
        "doctor_specialization": "Dermatologist",
        "doctor_qualification": "MBBS, MD (Dermatology)",
        "doctor_fee": 700.00,
    }

    res = client.post("/api/clinics/onboard", json=onboard_payload)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verify returned clinic data
    clinic_data = data["clinic"]
    assert clinic_data["name"] == onboard_payload["name"]
    assert clinic_data["slug"] == onboard_payload["slug"]
    assert clinic_data["consultation_fee_default"] == 600.00
    assert data["admin_user"]["email"] == onboard_payload["admin_email"].lower()
    assert data["admin_user"]["role"] == "ADMIN"
    assert data["doctor_user"]["email"] == onboard_payload["doctor_email"].lower()

    # Verify database state and public profile
    clinic_in_db = db_session.query(Clinic).filter(Clinic.id == clinic_data["id"]).first()
    assert clinic_in_db is not None
    pub_res = client.get(f"/api/clinics/public/{clinic_data['slug']}")
    assert pub_res.status_code == 200
    assert len(pub_res.json()["data"]["departments"]) == 3

    # Verify audit log was recorded
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.clinic_id == clinic_data["id"],
        AuditLog.action == "CLINIC_ONBOARDED"
    ).first()
    assert audit_entry is not None
    assert audit_entry.user_email == onboard_payload["admin_email"].lower()

    # Test login with newly onboarded admin
    login_res = client.post("/api/auth/login", json={
        "email": onboard_payload["admin_email"],
        "password": onboard_payload["admin_password"],
    })
    assert login_res.status_code == 200
    login_data = login_res.json()["data"]
    assert login_data["user"]["clinic_id"] == clinic_data["id"]
    assert login_data["user"]["clinic_name"] == clinic_data["name"]
    assert "view_audit_logs" in login_data["user"]["permissions"]


def test_public_clinic_profile(client):
    """Test public clinic microsite lookup by slug without leaking private credentials."""
    # Lookup default clinic
    res = client.get("/api/clinics/public/cliniccare-central")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "ClinicCare Multispeciality Hospital"
    assert "departments" in data
    assert "password" not in str(data)
    assert "password_hash" not in str(data)


def test_tenant_isolation_and_audit_access_control(client):
    """Test RBAC and multi-tenant security on audit logs."""
    # 1. Front Desk login
    fd_login = client.post("/api/auth/login", json={
        "email": "frontdesk@hospital.com",
        "password": "FrontDesk@123"
    })
    assert fd_login.status_code == 200
    fd_token = fd_login.json()["data"]["access_token"]

    # Front Desk CANNOT access admin audit logs (must return 403)
    fd_audit = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {fd_token}"})
    assert fd_audit.status_code == 403, f"Front desk should receive 403 on audit logs, got {fd_audit.status_code}"

    # 2. Patient login
    p_login = client.post("/api/auth/login", json={
        "email": "patient@hospital.com",
        "password": "Patient@123"
    })
    assert p_login.status_code == 200
    p_token = p_login.json()["data"]["access_token"]

    # Patient CANNOT access admin audit logs (must return 403)
    p_audit = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {p_token}"})
    assert p_audit.status_code == 403, f"Patient should receive 403 on audit logs, got {p_audit.status_code}"

    # 3. Admin login
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@hospital.com",
        "password": "Admin@123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["data"]["access_token"]

    # Admin CAN access audit logs
    admin_audit = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_audit.status_code == 200
    audit_data = admin_audit.json()["data"]
    assert isinstance(audit_data, list)
    assert len(audit_data) > 0


def test_patient_cross_access_prevented(client):
    """Verify that a patient cannot access or modify unauthorized patient data."""
    # Patient login
    p_login = client.post("/api/auth/login", json={
        "email": "patient@hospital.com",
        "password": "Patient@123"
    })
    p_token = p_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {p_token}"}

    # Patient cannot access admin stats
    res = client.get("/api/admin/stats", headers=headers)
    assert res.status_code == 403

    # Patient cannot access admin patients directory
    res2 = client.get("/api/admin/patients", headers=headers)
    assert res2.status_code == 403

    # Patient cannot access admin error logs
    res3 = client.get("/api/admin/errors", headers=headers)
    assert res3.status_code == 403


def test_cross_clinic_tenant_isolation_blocked(client, db_session):
    """Verify that Clinic A cannot access or modify Clinic B appointments (BOLA / IDOR protection)."""
    t = int(time.time())
    # 1. Onboard Clinic Alpha
    ca_payload = {
        "name": f"Clinic Alpha {t}",
        "slug": f"clinic-alpha-{t}",
        "phone": "+91 91111 11111",
        "email": f"alpha_{t}@hospital.in",
        "admin_name": f"Admin Alpha {t}",
        "admin_email": f"admin_alpha_{t}@hospital.in",
        "admin_password": "AlphaPassword@123",
        "doctor_name": f"Dr. Alpha {t}",
        "doctor_email": f"dr_alpha_{t}@hospital.in",
    }
    res_a = client.post("/api/clinics/onboard", json=ca_payload)
    assert res_a.status_code == 201
    clinic_a_id = res_a.json()["data"]["clinic"]["id"]

    # 2. Onboard Clinic Beta
    cb_payload = {
        "name": f"Clinic Beta {t}",
        "slug": f"clinic-beta-{t}",
        "phone": "+91 92222 22222",
        "email": f"beta_{t}@hospital.in",
        "admin_name": f"Admin Beta {t}",
        "admin_email": f"admin_beta_{t}@hospital.in",
        "admin_password": "BetaPassword@123",
        "doctor_name": f"Dr. Beta {t}",
        "doctor_email": f"dr_beta_{t}@hospital.in",
    }
    res_b = client.post("/api/clinics/onboard", json=cb_payload)
    assert res_b.status_code == 201
    clinic_b_id = res_b.json()["data"]["clinic"]["id"]
    doc_b_user_id = res_b.json()["data"]["doctor_user"]["id"]

    # Retrieve doctor profile for Beta
    doc_beta = db_session.query(Doctor).filter(Doctor.user_id == doc_b_user_id).first()
    assert doc_beta is not None

    # Retrieve a patient
    patient = db_session.query(Patient).first()
    assert patient is not None

    # Create an appointment in Clinic Beta
    from datetime import date, timedelta
    app_date = date.today() + timedelta(days=7)
    app_beta = Appointment(
        clinic_id=clinic_b_id,
        patient_id=patient.id,
        doctor_id=doc_beta.id,
        department_id=doc_beta.department_id,
        appointment_date=app_date,
        appointment_time="11:00",
        status="confirmed",
        reason="Beta clinic consultation",
    )
    db_session.add(app_beta)
    db_session.commit()
    db_session.refresh(app_beta)

    # Login as Admin Alpha
    login_a = client.post("/api/auth/login", json={
        "email": ca_payload["admin_email"],
        "password": ca_payload["admin_password"]
    })
    token_a = login_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Login as Admin Beta
    login_b = client.post("/api/auth/login", json={
        "email": cb_payload["admin_email"],
        "password": cb_payload["admin_password"]
    })
    token_b = login_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # TEST: Admin Alpha tries to read Clinic Beta's appointment -> MUST BE BLOCKED (403)
    get_res = client.get(f"/api/appointments/{app_beta.id}", headers=headers_a)
    assert get_res.status_code == 403, f"Expected 403 cross-tenant block, got {get_res.status_code}"

    # TEST: Admin Alpha tries to reschedule Clinic Beta's appointment -> MUST BE BLOCKED (403)
    resched_res = client.patch(
        f"/api/appointments/{app_beta.id}/reschedule",
        headers=headers_a,
        json={"new_date": str(app_date + timedelta(days=1)), "new_time": "12:00", "reason": "Unauthorized reschedule"}
    )
    assert resched_res.status_code == 403, f"Expected 403 cross-tenant block on reschedule, got {resched_res.status_code}"

    # TEST: Admin Alpha tries to cancel Clinic Beta's appointment -> MUST BE BLOCKED (403)
    cancel_res = client.patch(
        f"/api/appointments/{app_beta.id}/cancel",
        headers=headers_a,
        json={"reason": "Unauthorized cancellation"}
    )
    assert cancel_res.status_code == 403, f"Expected 403 cross-tenant block on cancel, got {cancel_res.status_code}"

    # TEST: Admin Beta (legitimate tenant) CAN view their own appointment -> SUCCESS (200)
    beta_get = client.get(f"/api/appointments/{app_beta.id}", headers=headers_b)
    assert beta_get.status_code == 200
    assert beta_get.json()["data"]["id"] == app_beta.id

