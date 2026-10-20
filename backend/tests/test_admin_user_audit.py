import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from app.models.user import User, EmailVerification
from app.models.security_privacy import SecurityEvent, UserSession
from app.core.security import get_password_hash


def test_password_login_audit_success(client, seed_test_data, db_session):
    login_payload = {
        "email": "patient@hospital.com",
        "password": "Patient@123"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["last_login_at"] is not None

    # Verify user record updated in database
    user = db_session.query(User).filter(User.email == "patient@hospital.com").first()
    assert user.last_login_at is not None
    assert user.failed_login_attempts == 0

    # Verify security audit event recorded
    event = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_email == "patient@hospital.com",
        SecurityEvent.event_type == "LOGIN_SUCCESS"
    ).first()
    assert event is not None
    assert event.severity == "INFO"
    assert "password" in event.details
    # Ensure sensitive credentials are NEVER logged
    assert "Patient@123" not in event.details
    assert "password_hash" not in event.details


def test_password_login_audit_failure(client, seed_test_data, db_session):
    login_payload = {
        "email": "patient@hospital.com",
        "password": "WrongPassword123!"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 401

    # Verify failed login attempts counter incremented
    user = db_session.query(User).filter(User.email == "patient@hospital.com").first()
    assert user.failed_login_attempts >= 1

    # Verify LOGIN_FAILED security event logged
    event = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_email == "patient@hospital.com",
        SecurityEvent.event_type == "LOGIN_FAILED"
    ).first()
    assert event is not None
    assert event.severity == "WARNING"
    # Ensure raw password attempt is NEVER logged
    assert "WrongPassword123!" not in event.details


def test_login_otp_audit_success_and_failure(client, seed_test_data, db_session):
    email = "patient@hospital.com"
    otp_code = "654321"

    # Pre-seed valid login OTP
    ev = EmailVerification(
        email=email,
        otp_hash=get_password_hash(otp_code),
        attempts=0,
        max_attempts=5,
        is_verified=False,
        purpose="login",
        expires_at=datetime.now(timezone.utc),
    )
    from datetime import timedelta
    ev.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.add(ev)
    db_session.commit()

    # 1. Test wrong OTP failure
    fail_resp = client.post("/api/auth/login/verify-otp", json={"email": email, "otp": "000000"})
    assert fail_resp.status_code == 400

    fail_event = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_email == email,
        SecurityEvent.event_type == "LOGIN_FAILED"
    ).first()
    assert fail_event is not None
    assert "000000" not in fail_event.details

    # 2. Test correct OTP success
    success_resp = client.post("/api/auth/login/verify-otp", json={"email": email, "otp": otp_code})
    assert success_resp.status_code == 200
    assert success_resp.json()["data"]["user"]["last_login_at"] is not None

    success_event = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_email == email,
        SecurityEvent.event_type == "LOGIN_SUCCESS"
    ).order_by(SecurityEvent.created_at.desc()).first()
    assert success_event is not None
    assert "email_otp" in success_event.details
    assert otp_code not in success_event.details


def test_google_login_audit(client, seed_test_data, db_session):
    mock_payload = {
        "email": "googletest@hospital.com",
        "email_verified": True,
        "name": "Google Test User",
        "picture": "https://example.com/pic.jpg",
        "iss": "https://accounts.google.com",
        "aud": "mock-aud",
    }

    with patch("app.services.auth_service.AuthService._fetch_google_token_info", return_value=mock_payload):
        resp = client.post("/api/auth/google", json={"id_token": "mock-secret-token", "role": "PATIENT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        event = db_session.query(SecurityEvent).filter(
            SecurityEvent.user_email == "googletest@hospital.com",
            SecurityEvent.event_type == "LOGIN_SUCCESS"
        ).first()
        assert event is not None
        assert "google_sso" in event.details
        # Raw token must not be in audit logs
        assert "mock-secret-token" not in event.details


def test_logout_session_revocation(client, seed_test_data, db_session):
    # 1. Login to get a valid token with a tracked session
    login_resp = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify token is initially active and works
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # 3. Call server-side logout endpoint
    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # 4. Verify LOGOUT security event recorded
    logout_event = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_email == "patient@hospital.com",
        SecurityEvent.event_type == "LOGOUT"
    ).first()
    assert logout_event is not None

    # 5. Verify the SAME token is now REJECTED with 401 Unauthorized
    rejected_resp = client.get("/api/auth/me", headers=headers)
    assert rejected_resp.status_code == 401
    assert "revoked" in rejected_resp.json()["detail"].lower() or "terminated" in rejected_resp.json()["detail"].lower()


def test_admin_user_directory_rbac(client, seed_test_data):
    # 1. Unauthenticated request rejected
    resp_unauth = client.get("/api/admin/users")
    assert resp_unauth.status_code == 401

    # 2. Patient role rejected
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    resp_pat = client.get("/api/admin/users", headers={"Authorization": f"Bearer {pat_token}"})
    assert resp_pat.status_code == 403

    # 3. Admin role authorized
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    resp_admin = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    data = resp_admin.json()["data"]
    assert "total" in data
    assert "users" in data
    assert data["total"] >= 3


def test_admin_user_search_and_filters(client, seed_test_data):
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Search by full name
    search_resp = client.get("/api/admin/users", params={"search": "John Patient"}, headers=headers)
    assert search_resp.status_code == 200
    search_users = search_resp.json()["data"]["users"]
    assert len(search_users) == 1
    assert search_users[0]["email"] == "patient@hospital.com"

    # Filter by role
    doc_resp = client.get("/api/admin/users", params={"role": "DOCTOR"}, headers=headers)
    assert doc_resp.status_code == 200
    for u in doc_resp.json()["data"]["users"]:
        assert u["role"] == "DOCTOR"

    # Filter by is_active
    active_resp = client.get("/api/admin/users", params={"is_active": True}, headers=headers)
    assert active_resp.status_code == 200
    for u in active_resp.json()["data"]["users"]:
        assert u["is_active"] is True


def test_admin_user_status_activation_deactivation(client, seed_test_data, db_session):
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    patient_user = db_session.query(User).filter(User.email == "patient@hospital.com").first()

    # 1. Admin deactivates patient
    deactivate_resp = client.patch(
        f"/api/admin/users/{patient_user.id}/status",
        json={"is_active": False, "reason": "Security hold"},
        headers=headers
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["data"]["is_active"] is False

    # 2. Deactivated user cannot login
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert pat_login.status_code == 403

    # 3. Admin reactivates patient
    activate_resp = client.patch(
        f"/api/admin/users/{patient_user.id}/status",
        json={"is_active": True, "reason": "Verification complete"},
        headers=headers
    )
    assert activate_resp.status_code == 200
    assert activate_resp.json()["data"]["is_active"] is True

    # 4. Reactivated user can now login
    pat_login_success = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert pat_login_success.status_code == 200


def test_admin_cannot_deactivate_last_active_admin(client, seed_test_data, db_session):
    admin_user = db_session.query(User).filter(User.email == "admin@hospital.com").first()
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Attempt to deactivate the only administrator
    resp = client.patch(
        f"/api/admin/users/{admin_user.id}/status",
        json={"is_active": False, "reason": "Self test"},
        headers=headers
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "last active administrator" in detail or "cannot deactivate" in detail


def test_admin_cannot_deactivate_self(client, seed_test_data, db_session):
    # Add a second admin so it's not the last admin
    second_admin = User(
        email="admin2@hospital.com",
        password_hash=get_password_hash("Admin@456"),
        full_name="Second Admin",
        role="ADMIN",
        is_active=True,
    )
    db_session.add(second_admin)
    db_session.commit()

    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    admin_user = db_session.query(User).filter(User.email == "admin@hospital.com").first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Attempt to deactivate self
    resp = client.patch(
        f"/api/admin/users/{admin_user.id}/status",
        json={"is_active": False},
        headers=headers
    )
    assert resp.status_code == 400
    assert "own account" in resp.json()["detail"].lower()


def test_admin_login_activity_endpoint(client, seed_test_data, db_session):
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Non-admin forbidden
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    forbidden_resp = client.get("/api/admin/security/login-activity", headers={"Authorization": f"Bearer {pat_token}"})
    assert forbidden_resp.status_code == 403

    # 2. Admin can list activity
    resp = client.get("/api/admin/security/login-activity", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1

    # 3. Filter by event_type
    filtered_resp = client.get("/api/admin/security/login-activity", params={"event_type": "LOGIN_SUCCESS"}, headers=headers)
    assert filtered_resp.status_code == 200
    for item in filtered_resp.json()["data"]["items"]:
        assert item["event_type"] == "LOGIN_SUCCESS"
