import pytest
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, Patient
from app.models.clinic import Clinic
from app.models.security_privacy import UserSession, PatientConsent, PrivacyRequest, SecurityEvent
from app.services.security_privacy_service import security_privacy_service


@pytest.fixture
def sec_test_setup(db_session):
    clinic = Clinic(name="Apollo Central", slug="apollo-sec", is_active=True)
    db_session.add(clinic)
    db_session.flush()

    admin = User(
        email="sec_admin@apollo.com",
        password_hash=get_password_hash("AdminPass@123"),
        full_name="Security Admin",
        role="ADMIN",
        clinic_id=clinic.id,
        is_active=True,
    )
    db_session.add(admin)
    db_session.flush()

    user_a = User(
        email="patient_a@apollo.com",
        password_hash=get_password_hash("PatientPass@123"),
        full_name="Patient Alice",
        role="PATIENT",
        clinic_id=clinic.id,
        is_active=True,
    )
    user_b = User(
        email="patient_b@apollo.com",
        password_hash=get_password_hash("PatientPass@123"),
        full_name="Patient Bob",
        role="PATIENT",
        clinic_id=clinic.id,
        is_active=True,
    )
    staff = User(
        email="nurse_priya@apollo.com",
        password_hash=get_password_hash("NursePass@123"),
        full_name="Nurse Priya",
        role="NURSE",
        clinic_id=clinic.id,
        is_active=True,
    )
    db_session.add_all([user_a, user_b, staff])
    db_session.flush()

    patient_a = Patient(user_id=user_a.id, blood_group="B+", gender="female")
    patient_b = Patient(user_id=user_b.id, blood_group="O+", gender="male")
    db_session.add_all([patient_a, patient_b])
    db_session.commit()

    return {
        "clinic": clinic,
        "admin": admin,
        "user_a": user_a,
        "patient_a": patient_a,
        "user_b": user_b,
        "patient_b": patient_b,
        "staff": staff,
    }


def auth_header_with_jti(user: User, jti: str) -> dict:
    tok = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role, "jti": jti})
    return {"Authorization": f"Bearer {tok}"}


def test_user_active_sessions_and_logout(client, sec_test_setup, db_session):
    user = sec_test_setup["user_a"]
    jti_1 = "test-jti-session-1"
    jti_2 = "test-jti-session-2"

    # Create 2 sessions
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    s1 = UserSession(user_id=user.id, token_jti=jti_1, ip_address="127.0.0.1", user_agent="Chrome/Test", is_active=True, last_activity_at=now, expires_at=now + timedelta(hours=2))
    s2 = UserSession(user_id=user.id, token_jti=jti_2, ip_address="192.168.1.10", user_agent="Safari/Test", is_active=True, last_activity_at=now, expires_at=now + timedelta(hours=2))
    db_session.add_all([s1, s2])
    db_session.commit()

    headers_1 = auth_header_with_jti(user, jti_1)

    # 1. List active sessions
    resp = client.get("/api/security/sessions", headers=headers_1)
    assert resp.status_code == 200
    sessions = resp.json()["data"]
    assert len(sessions) == 2

    # 2. Terminate current session
    logout_resp = client.post("/api/security/sessions/logout-current", headers=headers_1)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["data"]["status"] == "revoked"

    # 3. Subsequent request with revoked token fails with 401
    verify_resp = client.get("/api/security/sessions", headers=headers_1)
    assert verify_resp.status_code == 401
    assert "terminated or revoked" in verify_resp.json()["detail"].lower()

    # 4. Session 2 is still valid
    headers_2 = auth_header_with_jti(user, jti_2)
    verify_s2 = client.get("/api/security/sessions", headers=headers_2)
    assert verify_s2.status_code == 200
    assert len(verify_s2.json()["data"]) == 1

    # 5. Logout all sessions
    resp_all = client.post("/api/security/sessions/logout-all", headers=headers_2)
    assert resp_all.status_code == 200
    assert resp_all.json()["data"]["revoked_count"] >= 1

    # Now Session 2 also fails with 401
    verify_s2_again = client.get("/api/security/sessions", headers=headers_2)
    assert verify_s2_again.status_code == 401


def test_password_change_and_security_events(client, sec_test_setup):
    user = sec_test_setup["user_a"]
    jti = "jti-pw-test"
    headers = auth_header_with_jti(user, jti)

    # 1. Invalid old password fails
    fail_payload = {"old_password": "WrongPassword123", "new_password": "NewSecurePassword@99"}
    resp_fail = client.post("/api/security/change-password", json=fail_payload, headers=headers)
    assert resp_fail.status_code == 400
    assert "incorrect" in resp_fail.json()["detail"].lower()

    # 2. Correct old password succeeds
    success_payload = {"old_password": "PatientPass@123", "new_password": "NewSecurePassword@99"}
    resp_ok = client.post("/api/security/change-password", json=success_payload, headers=headers)
    assert resp_ok.status_code == 200
    assert resp_ok.json()["success"] is True

    # 3. Check security events audit
    events_resp = client.get("/api/security/events", headers=headers)
    assert events_resp.status_code == 200
    events = events_resp.json()["data"]
    event_types = [e["event_type"] for e in events]
    assert "PASSWORD_CHANGE" in event_types
    assert "PASSWORD_CHANGE_FAILED" in event_types


def test_staff_activation_and_deactivation(client, sec_test_setup):
    admin = sec_test_setup["admin"]
    staff = sec_test_setup["staff"]
    admin_headers = auth_header_with_jti(admin, "jti-admin")
    staff_headers = auth_header_with_jti(staff, "jti-staff")

    # 1. Staff is currently active
    resp_staff_me = client.get("/api/auth/me", headers=staff_headers)
    assert resp_staff_me.status_code == 200

    # 2. Admin deactivates staff
    deact_resp = client.post(
        f"/api/security/staff/{staff.id}/status",
        json={"is_active": False, "reason": "Staff leave of absence"},
        headers=admin_headers,
    )
    assert deact_resp.status_code == 200
    assert deact_resp.json()["data"]["is_active"] is False

    # 3. Staff token is now forbidden (account disabled)
    resp_disabled = client.get("/api/auth/me", headers=staff_headers)
    assert resp_disabled.status_code == 403
    assert "disabled" in resp_disabled.json()["detail"].lower()

    # 4. Admin reactivates staff
    react_resp = client.post(
        f"/api/security/staff/{staff.id}/status",
        json={"is_active": True, "reason": "Staff returned to duties"},
        headers=admin_headers,
    )
    assert react_resp.status_code == 200
    assert react_resp.json()["data"]["is_active"] is True


def test_patient_consent_lifecycle(client, sec_test_setup):
    user_a = sec_test_setup["user_a"]
    admin = sec_test_setup["admin"]
    headers_a = auth_header_with_jti(user_a, "jti-consent-a")
    admin_headers = auth_header_with_jti(admin, "jti-consent-admin")

    # 1. Grant consent
    consent_payload = {
        "consent_type": "TELEMEDICINE_CONSENT",
        "purpose": "Audio/video medical consultation and remote vital parameter evaluation",
        "source": "PATIENT_PORTAL",
    }
    grant_resp = client.post("/api/consents", json=consent_payload, headers=headers_a)
    assert grant_resp.status_code == 201
    consent_data = grant_resp.json()["data"]
    consent_id = consent_data["id"]
    assert consent_data["status"] == "GRANTED"
    assert consent_data["consent_type"] == "TELEMEDICINE_CONSENT"

    # 2. Patient lists their consents
    my_consents = client.get("/api/consents/my", headers=headers_a)
    assert my_consents.status_code == 200
    assert len(my_consents.json()["data"]) >= 1

    # 3. Withdraw consent
    withdraw_payload = {"reason": "Patient decided to only consult in-person"}
    withdraw_resp = client.post(f"/api/consents/{consent_id}/withdraw", json=withdraw_payload, headers=headers_a)
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.json()["data"]["status"] == "REVOKED"
    assert withdraw_resp.json()["data"]["revoked_at"] is not None

    # 4. Admin lists clinic consents
    admin_list = client.get("/api/admin/consents", headers=admin_headers)
    assert admin_list.status_code == 200
    ids = [c["id"] for c in admin_list.json()["data"]]
    assert consent_id in ids


def test_privacy_data_export_and_deletion_workflows(client, sec_test_setup):
    user_a = sec_test_setup["user_a"]
    admin = sec_test_setup["admin"]
    headers_a = auth_header_with_jti(user_a, "jti-privacy-a")
    admin_headers = auth_header_with_jti(admin, "jti-privacy-admin")

    # 1. Data Export Request
    export_resp = client.post("/api/privacy/export-request", json={"request_type": "DATA_EXPORT", "reason": "Moving abroad"}, headers=headers_a)
    assert export_resp.status_code == 201
    export_data = export_resp.json()["data"]
    assert export_data["status"] == "COMPLETED"
    assert export_data["export_payload"] is not None
    assert export_data["export_payload"]["patient"]["email"] == user_a.email

    # 2. Data Deletion Request (with statutory retention warning)
    del_resp = client.post("/api/privacy/deletion-request", json={"request_type": "DATA_DELETION", "reason": "Privacy preference"}, headers=headers_a)
    assert del_resp.status_code == 201
    del_data = del_resp.json()["data"]
    assert del_data["status"] == "PENDING"
    assert "retention" in del_data["retention_note"].lower()
    del_request_id = del_data["id"]

    # 3. Patient views their own privacy requests
    my_reqs = client.get("/api/privacy/requests/my", headers=headers_a)
    assert my_reqs.status_code == 200
    assert len(my_reqs.json()["data"]) >= 2

    # 4. Admin processes deletion request
    process_payload = {
        "status": "COMPLETED",
        "retention_note": "Account credentials and profile deactivated. Clinical charts archived securely under statutory NMC retention schedule."
    }
    proc_resp = client.post(f"/api/admin/privacy/requests/{del_request_id}/process", json=process_payload, headers=admin_headers)
    assert proc_resp.status_code == 200
    assert proc_resp.json()["data"]["status"] == "COMPLETED"


def test_cross_patient_privacy_isolation(client, sec_test_setup):
    user_a = sec_test_setup["user_a"]
    user_b = sec_test_setup["user_b"]
    headers_a = auth_header_with_jti(user_a, "jti-a")
    headers_b = auth_header_with_jti(user_b, "jti-b")

    # Patient A creates a consent
    c_res = client.post("/api/consents", json={"consent_type": "COMMUNICATION_CONSENT", "purpose": "SMS Reminders"}, headers=headers_a)
    consent_id = c_res.json()["data"]["id"]

    # Patient B CANNOT withdraw Patient A's consent
    resp_hack = client.post(f"/api/consents/{consent_id}/withdraw", json={"reason": "Malicious attempt"}, headers=headers_b)
    assert resp_hack.status_code == 404

    # Patient A CANNOT access admin privacy requests
    resp_admin = client.get("/api/admin/privacy/requests", headers=headers_a)
    assert resp_admin.status_code == 403

    # Patient A CANNOT access admin consents
    resp_admin_consents = client.get("/api/admin/consents", headers=headers_a)
    assert resp_admin_consents.status_code == 403
