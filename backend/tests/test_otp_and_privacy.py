import pytest
from app.models.user import User, Patient, EmailVerification
from app.models.report import Report
from app.models.appointment import Appointment
from datetime import date, timedelta


def test_otp_registration_lifecycle_and_privacy(client, db_session, seed_test_data):
    test_email = "newpatient_otp_test@hospital.com"

    # Clean up prior test data if exists
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    u = db_session.query(User).filter(User.email == test_email).first()
    if u:
        db_session.delete(u)
    db_session.commit()

    # 1. Step 1: Send OTP
    res = client.post("/api/auth/register/send-otp", json={"email": test_email, "full_name": "Test Patient"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "email" in data
    assert data["email"] == test_email
    otp_code = data.get("dev_code")
    assert otp_code is not None, "dev_code must be provided in test environment"

    # 2. Rate-limit check: requesting immediately again should be rejected
    res_rate = client.post("/api/auth/register/send-otp", json={"email": test_email, "full_name": "Test Patient"})
    assert res_rate.status_code == 400
    assert "wait" in res_rate.json()["detail"].lower()

    # 3. Invalid OTP rejection
    res_invalid = client.post("/api/auth/register/verify-otp", json={"email": test_email, "otp": "000000"})
    assert res_invalid.status_code == 400
    assert "invalid" in res_invalid.json()["detail"].lower()

    # 4. Valid OTP verification
    res_valid = client.post("/api/auth/register/verify-otp", json={"email": test_email, "otp": otp_code})
    assert res_valid.status_code == 200
    assert res_valid.json()["data"]["verified"] is True

    # 5. Complete Registration
    res_reg = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": "Password@123",
            "full_name": "Test Patient",
            "phone": "+15559876543",
            "gender": "male",
            "blood_group": "A+",
            "otp": otp_code,
        }
    )
    assert res_reg.status_code == 201
    patient_a_token = res_reg.json()["data"]["access_token"]
    patient_a_id = res_reg.json()["data"]["user"]["patient_profile"]["id"]
    assert patient_a_token is not None

    # 6. Duplicate registration rejection
    res_dup = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": "Password@123",
            "full_name": "Test Patient",
        }
    )
    assert res_dup.status_code == 400

    # 7. Role escalation rejection (trying to register as ADMIN or DOCTOR)
    res_esc = client.post(
        "/api/auth/register",
        json={
            "email": "hacker@test.com",
            "password": "Password@123",
            "full_name": "Hacker User",
            "role": "ADMIN",
        }
    )
    assert res_esc.status_code == 400
    assert "administrative" in res_esc.json()["detail"].lower()

    # 8. Patient Privacy (Example A & B from spec):
    # Patient A cannot browse general patient directory
    res_browse = client.get("/api/patients", headers={"Authorization": f"Bearer {patient_a_token}"})
    assert res_browse.status_code == 403

    # Patient A cannot view Patient B's profile
    patient_b = seed_test_data["patient"]
    res_cross_profile = client.get(
        f"/api/patients/{patient_b.id}",
        headers={"Authorization": f"Bearer {patient_a_token}"}
    )
    assert res_cross_profile.status_code == 403

    # Patient A CAN view their own profile
    res_own_profile = client.get(
        f"/api/patients/{patient_a_id}",
        headers={"Authorization": f"Bearer {patient_a_token}"}
    )
    assert res_own_profile.status_code == 200
    assert res_own_profile.json()["data"]["id"] == patient_a_id

    # Patient A cannot call Admin stats
    res_admin_block = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {patient_a_token}"})
    assert res_admin_block.status_code == 403

    # Patient A cannot call Doctor appointments
    res_doc_block = client.get("/api/doctor/appointments", headers={"Authorization": f"Bearer {patient_a_token}"})
    assert res_doc_block.status_code == 403

    # Front Desk cannot call Admin errors
    from app.core.security import get_password_hash
    fd_user = User(
        email="frontdesk_test@hospital.com",
        password_hash=get_password_hash("FrontDesk@123"),
        full_name="Front Desk Test",
        role="FRONT_DESK",
        is_active=True,
    )
    db_session.add(fd_user)
    db_session.commit()

    fd_login = client.post("/api/auth/login", json={"email": "frontdesk_test@hospital.com", "password": "FrontDesk@123"})
    assert fd_login.status_code == 200
    fd_token = fd_login.json()["data"]["access_token"]
    res_fd_errors = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {fd_token}"})
    assert res_fd_errors.status_code == 403

    # Admin CAN call Admin stats and errors
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["data"]["access_token"]
    res_admin_errors = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_errors.status_code == 200
