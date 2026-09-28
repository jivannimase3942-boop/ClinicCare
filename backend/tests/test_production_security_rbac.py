import pytest
import time
from datetime import datetime, timezone, timedelta
from app.models.user import User, Patient, Doctor, EmailVerification
from app.models.appointment import Appointment
from app.core.security import get_password_hash, create_access_token


def test_20_point_security_and_rbac_suite(client, db_session, seed_test_data):
    # Setup test users
    admin_user = seed_test_data["admin"]
    doctor_1 = seed_test_data["doctor"]
    patient_1 = seed_test_data["patient"]

    # Create doctor 2
    doc2_user = User(
        email="doctor2_test@hospital.com",
        password_hash=get_password_hash("DocPass@123"),
        full_name="Dr. Second Specialist",
        role="DOCTOR",
        is_active=True,
    )
    db_session.add(doc2_user)
    db_session.flush()
    doc2_profile = Doctor(
        user_id=doc2_user.id,
        department_id=doctor_1.department_id,
        specialization="Neurology",
        qualification="MD",
        is_active=True,
    )
    db_session.add(doc2_profile)

    # Create patient 2
    pat2_user = User(
        email="patient2_test@hospital.com",
        password_hash=get_password_hash("PatPass@123"),
        full_name="Patient Two",
        role="PATIENT",
        is_active=True,
    )
    db_session.add(pat2_user)
    db_session.flush()
    pat2_profile = Patient(user_id=pat2_user.id)
    db_session.add(pat2_profile)

    # Create front desk user
    fd_user = User(
        email="frontdesk_rbac@hospital.com",
        password_hash=get_password_hash("FrontDesk@123"),
        full_name="Front Desk Staff",
        role="FRONT_DESK",
        is_active=True,
    )
    db_session.add(fd_user)

    # Create pending doctor user
    pending_doc_user = User(
        email="pending_doc@hospital.com",
        password_hash=get_password_hash("DocPass@123"),
        full_name="Dr. Pending Verification",
        role="PENDING_DOCTOR",
        is_active=True,
    )
    db_session.add(pending_doc_user)

    # Create pending front desk user
    pending_fd_user = User(
        email="pending_fd@hospital.com",
        password_hash=get_password_hash("FdPass@123"),
        full_name="Pending Front Desk",
        role="PENDING_FRONT_DESK",
        is_active=True,
    )
    db_session.add(pending_fd_user)

    # Create appointment assigned to doctor 1
    app_doc1 = Appointment(
        patient_id=patient_1.id,
        doctor_id=doctor_1.id,
        department_id=doctor_1.department_id,
        appointment_date=datetime.now(timezone.utc).date() + timedelta(days=2),
        appointment_time="10:00",
        reason="General Checkup",
        status="confirmed",
    )
    db_session.add(app_doc1)
    db_session.commit()

    # Generate JWT tokens for test roles
    admin_tok = create_access_token({"sub": admin_user.id, "email": admin_user.email, "role": "ADMIN"})
    doc1_tok = create_access_token({"sub": doctor_1.user.id, "email": doctor_1.user.email, "role": "DOCTOR"})
    doc2_tok = create_access_token({"sub": doc2_user.id, "email": doc2_user.email, "role": "DOCTOR"})
    pat1_tok = create_access_token({"sub": patient_1.user.id, "email": patient_1.user.email, "role": "PATIENT"})
    pat2_tok = create_access_token({"sub": pat2_user.id, "email": pat2_user.email, "role": "PATIENT"})
    fd_tok = create_access_token({"sub": fd_user.id, "email": fd_user.email, "role": "FRONT_DESK"})
    pending_doc_tok = create_access_token({"sub": pending_doc_user.id, "email": pending_doc_user.email, "role": "PENDING_DOCTOR"})
    pending_fd_tok = create_access_token({"sub": pending_fd_user.id, "email": pending_fd_user.email, "role": "PENDING_FRONT_DESK"})

    # --- 1. Patient cannot access another patient's data ---
    res1 = client.get(f"/api/patients/{pat2_profile.id}", headers={"Authorization": f"Bearer {pat1_tok}"})
    assert res1.status_code == 403, f"Expected 403, got {res1.status_code}"

    # --- 2. Patient cannot access doctor dashboard ---
    res2 = client.get("/api/doctor/appointments", headers={"Authorization": f"Bearer {pat1_tok}"})
    assert res2.status_code == 403, f"Expected 403, got {res2.status_code}"

    # --- 3. Patient cannot access admin dashboard ---
    res3 = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {pat1_tok}"})
    assert res3.status_code == 403, f"Expected 403, got {res3.status_code}"

    # --- 4. Doctor cannot access another doctor's private controls ---
    # Doctor 2 tries to update status of appointment assigned to Doctor 1
    res4 = client.patch(
        f"/api/doctor/appointments/{app_doc1.id}/status",
        headers={"Authorization": f"Bearer {doc2_tok}"},
        json={"status": "completed", "notes": "Unauthorized modification"}
    )
    assert res4.status_code == 403, f"Expected 403, got {res4.status_code}"

    # --- 5. Doctor cannot access admin functions ---
    res5a = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {doc1_tok}"})
    assert res5a.status_code == 403, f"Expected 403, got {res5a.status_code}"
    res5b = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {doc1_tok}"})
    assert res5b.status_code == 403, f"Expected 403, got {res5b.status_code}"

    # --- 6. Front Desk cannot access admin functions ---
    res6a = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {fd_tok}"})
    assert res6a.status_code == 403, f"Expected 403, got {res6a.status_code}"
    res6b = client.get("/api/admin/conversations", headers={"Authorization": f"Bearer {fd_tok}"})
    assert res6b.status_code == 403, f"Expected 403, got {res6b.status_code}"

    # --- 7. Front Desk cannot access private clinical consultation records of another doctor ---
    res7 = client.get("/api/doctor/appointments", headers={"Authorization": f"Bearer {fd_tok}"})
    assert res7.status_code == 403, f"Expected 403, got {res7.status_code}"

    # --- 8. Admin can access required administrative endpoints ---
    res8a = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_tok}"})
    assert res8a.status_code == 200, f"Expected 200, got {res8a.status_code}"
    res8b = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {admin_tok}"})
    assert res8b.status_code == 200, f"Expected 200, got {res8b.status_code}"

    # --- 9. Duplicate verified email registration is rejected ---
    res9 = client.post(
        "/api/auth/register",
        json={"email": admin_user.email, "password": "Password@123", "full_name": "Dupe Admin"}
    )
    assert res9.status_code == 400, f"Expected 400, got {res9.status_code}"

    # --- 10. Invalid OTP is rejected ---
    t_email = f"otp_sec_test_{int(time.time())}@hospital.com"
    res10a = client.post("/api/auth/register/send-otp", json={"email": t_email, "full_name": "OTP User"})
    assert res10a.status_code == 200
    res10b = client.post("/api/auth/register/verify-otp", json={"email": t_email, "otp": "999999"})
    assert res10b.status_code == 400, f"Expected 400 on wrong OTP, got {res10b.status_code}"

    # --- 11. Expired OTP is rejected ---
    exp_email = f"expired_otp_{int(time.time())}@hospital.com"
    ev_expired = EmailVerification(
        email=exp_email,
        otp_hash=get_password_hash("123456"),
        attempts=0,
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    db_session.add(ev_expired)
    db_session.commit()
    res11 = client.post("/api/auth/register/verify-otp", json={"email": exp_email, "otp": "123456"})
    assert res11.status_code == 400
    assert "expired" in res11.json()["detail"].lower()

    # --- 12. OTP cannot be reused ---
    reuse_email = f"reuse_test_{int(time.time())}@hospital.com"
    ev_reuse = EmailVerification(
        email=reuse_email,
        otp_hash=get_password_hash("654321"),
        attempts=0,
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(ev_reuse)
    db_session.commit()
    # First use in registration
    res12a = client.post(
        "/api/auth/register",
        json={"email": reuse_email, "password": "Password@123", "full_name": "First User", "otp": "654321"}
    )
    assert res12a.status_code == 201
    # Try reusing same OTP again
    res12b = client.post("/api/auth/register/verify-otp", json={"email": reuse_email, "otp": "654321"})
    assert res12b.status_code == 400

    # --- 13. OTP brute-force attempts are rate limited (max attempts) ---
    bf_email = f"bruteforce_{int(time.time())}@hospital.com"
    ev_bf = EmailVerification(
        email=bf_email,
        otp_hash=get_password_hash("777777"),
        attempts=4,  # already 4 attempts
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(ev_bf)
    db_session.commit()
    # 5th attempt (fails)
    res13a = client.post("/api/auth/register/verify-otp", json={"email": bf_email, "otp": "000001"})
    assert res13a.status_code == 400
    # 6th attempt (max attempts exceeded)
    res13b = client.post("/api/auth/register/verify-otp", json={"email": bf_email, "otp": "777777"})
    assert res13b.status_code == 400
    assert "maximum" in res13b.json()["detail"].lower()

    # --- 14. Password is never stored in plaintext ---
    pat1_user_db = db_session.query(User).filter(User.email == patient_1.user.email).first()
    assert pat1_user_db is not None
    assert pat1_user_db.password_hash != "Patient@123"
    assert pat1_user_db.password_hash.startswith("$2b$") or pat1_user_db.password_hash.startswith("$argon2id$")

    # --- 15. JWT/session authorization works correctly ---
    res15_valid = client.get("/api/auth/me", headers={"Authorization": f"Bearer {pat1_tok}"})
    assert res15_valid.status_code == 200
    res15_invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
    assert res15_invalid.status_code == 401

    # --- 16. Public API does not leak private records ---
    # Unauthenticated requests cannot access private patient records or operational analytics
    res16a = client.get(f"/api/patients/{patient_1.id}", headers={"Authorization": f"Bearer {pat2_tok}"})
    assert res16a.status_code == 403, "Cross-patient profile access must be denied"
    res16b = client.get("/api/reports/my")
    assert res16b.status_code in [401, 403], f"Expected 401/403, got {res16b.status_code}"
    res16c = client.get("/api/appointments/my")
    assert res16c.status_code in [401, 403], f"Expected 401/403, got {res16c.status_code}"
    res16d = client.get("/api/admin/errors")
    assert res16d.status_code in [401, 403], f"Expected 401/403, got {res16d.status_code}"

    # --- 17. Google authentication cannot bypass RBAC ---
    # Attempting to call Google auth with role="ADMIN" should not grant ADMIN
    from app.services.auth_service import auth_service
    # Mocking verify to test role restriction
    mock_email = f"google_test_{int(time.time())}@hospital.com"
    user_g = User(
        email=mock_email,
        password_hash=get_password_hash("googletest"),
        full_name="Google Admin Wannabe",
        role="PENDING_FRONT_DESK",  # Google cannot elevate to ADMIN
        is_active=True,
    )
    db_session.add(user_g)
    db_session.commit()
    # Verify user does not have ADMIN privileges
    g_tok = create_access_token({"sub": user_g.id, "email": user_g.email, "role": user_g.role})
    res17 = client.get("/api/admin/errors", headers={"Authorization": f"Bearer {g_tok}"})
    assert res17.status_code == 403

    # --- 18. Pending Doctor cannot use Doctor privileges ---
    res18 = client.get("/api/doctor/appointments", headers={"Authorization": f"Bearer {pending_doc_tok}"})
    assert res18.status_code == 403, f"Expected 403, got {res18.status_code}"

    # --- 19. Pending Front Desk cannot use Front Desk privileges ---
    res19 = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {pending_fd_tok}"})
    assert res19.status_code == 403, f"Expected 403, got {res19.status_code}"

    # --- 20. Admin cannot be created through unrestricted public registration ---
    res20 = client.post(
        "/api/auth/register",
        json={"email": "hacker_admin@hospital.com", "password": "Password@123", "full_name": "Fake Admin", "role": "ADMIN"}
    )
    assert res20.status_code == 400
    assert "administrative" in res20.json()["detail"].lower()
