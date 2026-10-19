import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path for direct script execution and testing
_backend_path = str(Path(__file__).resolve().parent.parent)
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

import socket
import smtplib
from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.core.config import settings
from app.services.email_service import (
    EmailService,
    email_service,
    EmailNotConfiguredError,
    EmailConnectionError,
    EmailAuthenticationError,
    EmailDeliveryError,
    SMTPNotConfiguredError,
    SMTPConnectionError,
    SMTPAuthenticationError,
    SMTPDeliveryError,
    ResendNotConfiguredError,
    ResendConnectionError,
    ResendAuthenticationError,
    ResendDeliveryError,
)
from app.models.user import User, EmailVerification
from app.core.security import get_password_hash


@pytest.fixture(autouse=True)
def restore_settings():
    """Ensure settings are restored after each test."""
    orig_env = settings.ENVIRONMENT
    orig_provider = getattr(settings, "EMAIL_PROVIDER", "resend")
    orig_resend_key = getattr(settings, "RESEND_API_KEY", None)
    orig_resend_from = getattr(settings, "RESEND_FROM_EMAIL", None)
    orig_resend_url = getattr(settings, "RESEND_API_URL", "https://api.resend.com/emails")
    orig_resend_timeout = getattr(settings, "RESEND_TIMEOUT", 10.0)
    orig_host = settings.SMTP_HOST
    orig_port = settings.SMTP_PORT
    orig_user = settings.SMTP_USER
    orig_pass = settings.SMTP_PASSWORD
    orig_sender = settings.SMTP_SENDER
    orig_sender_name = getattr(settings, "SMTP_SENDER_NAME", "ClinicCare Healthcare")
    orig_use_ssl = getattr(settings, "SMTP_USE_SSL", False)
    orig_use_tls = getattr(settings, "SMTP_USE_TLS", True)
    orig_timeout = getattr(settings, "SMTP_TIMEOUT", 10)
    orig_debug = settings.DEBUG
    yield
    settings.ENVIRONMENT = orig_env
    settings.EMAIL_PROVIDER = orig_provider
    settings.RESEND_API_KEY = orig_resend_key
    settings.RESEND_FROM_EMAIL = orig_resend_from
    settings.RESEND_API_URL = orig_resend_url
    settings.RESEND_TIMEOUT = orig_resend_timeout
    settings.SMTP_HOST = orig_host
    settings.SMTP_PORT = orig_port
    settings.SMTP_USER = orig_user
    settings.SMTP_PASSWORD = orig_pass
    settings.SMTP_SENDER = orig_sender
    settings.SMTP_SENDER_NAME = orig_sender_name
    settings.SMTP_USE_SSL = orig_use_ssl
    settings.SMTP_USE_TLS = orig_use_tls
    settings.SMTP_TIMEOUT = orig_timeout
    settings.DEBUG = orig_debug


# ==============================================================================
# LEGACY SMTP TRANSPORT BACKWARD-COMPATIBILITY TESTS
# ==============================================================================

def test_smtp_delivery_success(client, db_session):
    """Verifies successful SMTP dispatch with full RFC headers and HTML/plain text parts."""
    test_email = "verified_delivery_test@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = "smtp.sendgrid.net"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "apikey"
    settings.SMTP_PASSWORD = "SG.test-secret-key-12345"
    settings.SMTP_SENDER = "noreply@cliniccarehospital.com"

    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_class:
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Test Patient"},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == test_email
        assert data["email_dispatched"] is True
        assert data["smtp_configured"] is True
        assert "dev_code" not in data

        mock_smtp_class.assert_called_with("smtp.sendgrid.net", 587, timeout=10)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("apikey", "SG.test-secret-key-12345")
        mock_smtp_instance.send_message.assert_called_once()

        sent_msg = mock_smtp_instance.send_message.call_args[0][0]
        assert "noreply@cliniccarehospital.com" in sent_msg["From"]
        assert sent_msg["To"] == test_email
        assert "ClinicCare Verification Code" in sent_msg["Subject"]


def test_smtp_missing_configuration_in_production(client, db_session):
    """
    Verifies that when SMTP is explicitly selected but unconfigured in production:
    1. EmailService raises SMTPNotConfiguredError.
    2. API returns HTTP 503 instead of false HTTP 200.
    3. dev_code is NEVER returned.
    """
    test_email = "unconfigured_smtp_prod@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = None
    settings.SMTP_USER = None
    settings.SMTP_PASSWORD = None

    with pytest.raises(SMTPNotConfiguredError) as exc_info:
        EmailService.send_email(
            to_email=test_email,
            subject="Test",
            text_content="Body",
        )
    assert "SMTP email service is not configured on this server" in str(exc_info.value)

    resp = client.post(
        "/api/auth/register/send-otp",
        json={"email": test_email, "full_name": "Prod Patient"},
    )
    assert resp.status_code == 503
    err_detail = resp.json()["detail"]
    assert "SMTP email service is not configured" in err_detail
    assert "SMTP_HOST, SMTP_USER, SMTP_PASSWORD" in err_detail


def test_smtp_provider_rejection_auth_failure(client, db_session):
    """Verifies that SMTP authentication rejections (e.g. 535) return HTTP 502 Bad Gateway."""
    test_email = "auth_fail_test@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = "smtp.gmail.com"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "user@gmail.com"
    settings.SMTP_PASSWORD = "badpassword"

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")

    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Auth Failure"},
        )
        assert resp.status_code == 502
        assert "SMTP authentication failed" in resp.json()["detail"]


def test_smtp_provider_rejection_recipient_refused(client, db_session):
    """Verifies that recipient rejection (e.g. 550 Mailbox unavailable) returns HTTP 502 Bad Gateway."""
    test_email = "rejected_recipient@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = "smtp.provider.com"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "mailer"
    settings.SMTP_PASSWORD = "secretpassword"

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    mock_smtp_instance.send_message.side_effect = smtplib.SMTPRecipientsRefused(
        {test_email: (550, b"User unknown / Mailbox unavailable")}
    )

    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Rejected User"},
        )
        assert resp.status_code == 502
        assert "rejected delivery" in resp.json()["detail"].lower()


def test_smtp_connection_failure(client, db_session):
    """Verifies that SMTP connection timeouts or refusal return HTTP 502 Bad Gateway."""
    test_email = "connection_fail_test@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = "smtp.unreachable-host.local"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "mailer"
    settings.SMTP_PASSWORD = "secretpassword"

    with patch("smtplib.SMTP", side_effect=socket.timeout("Connection timed out")):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Timeout User"},
        )
        assert resp.status_code == 502
        assert "Failed to connect to SMTP server" in resp.json()["detail"]


def test_smtp_development_fallback_with_dev_code(client, db_session):
    """In development mode with unconfigured SMTP, API should return 200 with dev_code."""
    test_email = "dev_mode_patient@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "development"
    settings.EMAIL_PROVIDER = "smtp"
    settings.DEBUG = True
    settings.SMTP_HOST = None
    settings.SMTP_USER = None
    settings.SMTP_PASSWORD = None

    resp = client.post(
        "/api/auth/register/send-otp",
        json={"email": test_email, "full_name": "Dev User"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == test_email
    assert data["email_dispatched"] is False
    assert data["smtp_configured"] is False
    assert data.get("dev_code") is not None
    assert len(data["dev_code"]) == 6


def test_smtp_status_and_health_endpoints(client):
    """Verifies safe SMTP diagnostic status reporting without credential leaks."""
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = "smtp.relay.example.com"
    settings.SMTP_PORT = 465
    settings.SMTP_USER = "smtp_admin"
    settings.SMTP_PASSWORD = "super_secret_value_do_not_leak"
    settings.SMTP_SENDER = "notifications@cliniccarehospital.com"
    settings.SMTP_USE_SSL = True

    resp = client.get("/api/auth/smtp-status")
    assert resp.status_code == 200
    status_data = resp.json()["data"]
    assert status_data["configured"] is True
    assert status_data["host"] == "smtp.relay.example.com"
    assert status_data["port"] == 465
    assert status_data["sender"] == "notifications@cliniccarehospital.com"
    assert status_data["use_ssl"] is True
    assert "super_secret" not in str(resp.json())

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["smtp_configured"] is True


def test_render_runtime_production_auto_detection_and_no_dev_code(client, monkeypatch):
    """Verifies that running in Render environment forces production mode and blocks dev_code."""
    monkeypatch.setenv("RENDER", "true")
    assert settings.is_production is True

    test_email = "render_test_patient@cliniccarehospital.com"
    settings.EMAIL_PROVIDER = "smtp"
    settings.SMTP_HOST = None
    settings.SMTP_USER = None
    settings.SMTP_PASSWORD = None

    resp = client.post(
        "/api/auth/register/send-otp",
        json={"email": test_email, "full_name": "Render Patient"},
    )
    assert resp.status_code == 503
    assert "SMTP email service is not configured on this server" in resp.json()["detail"]
    assert "dev_code" not in str(resp.json())


# ==============================================================================
# PHASE 4: RESEND HTTPS EMAIL API COMPREHENSIVE TESTS
# ==============================================================================

def test_resend_execute_post_invokes_httpx():
    """Verifies that EmailService._execute_resend_post uses httpx.Client with specified timeout."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = MagicMock(status_code=200)

    with patch("app.services.email_service.httpx.Client", return_value=mock_client):
        resp = EmailService._execute_resend_post(
            api_url="https://api.resend.com/emails",
            headers={"Authorization": "Bearer key"},
            payload={"from": "care@hospital.com", "to": ["pat@hospital.com"]},
            timeout=15.0,
        )
        assert resp.status_code == 200
        mock_client.post.assert_called_once_with(
            "https://api.resend.com/emails",
            headers={"Authorization": "Bearer key"},
            json={"from": "care@hospital.com", "to": ["pat@hospital.com"]},
        )


def test_1_resend_successful_request():
    """1. Successful Resend API request returns True."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_test_mock_api_key_123"
    settings.RESEND_FROM_EMAIL = "alerts@cliniccarehospital.com"

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_resp) as mock_post:
        success = EmailService.send_email(
            to_email="patient@example.com",
            subject="Verification Code",
            text_content="Your code is 123456",
        )
        assert success is True
        mock_post.assert_called_once()


def test_2_resend_correct_authorization_header_and_payload():
    """2. Verifies correct Authorization: Bearer <key> header and request JSON payload."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_secret_key_999"
    settings.RESEND_FROM_EMAIL = "care@cliniccarehospital.com"
    settings.SMTP_SENDER_NAME = "ClinicCare Multispeciality"

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"id": "resend_id_abc"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_resp) as mock_post:
        EmailService.send_email(
            to_email="patient@cliniccarehospital.com",
            subject="Welcome Patient",
            text_content="Plain text content",
            html_content="<p>HTML content</p>",
        )

        assert mock_post.called
        kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        call_url = kwargs.get("api_url") or mock_post.call_args[0][0]
        call_headers = kwargs.get("headers") or mock_post.call_args[0][1]
        call_json = kwargs.get("payload") or mock_post.call_args[0][2]

        assert call_url == "https://api.resend.com/emails"
        assert call_headers["Authorization"] == "Bearer re_secret_key_999"
        assert call_headers["Content-Type"] == "application/json"
        assert call_json["from"] == "ClinicCare Multispeciality <care@cliniccarehospital.com>"
        assert call_json["to"] == ["patient@cliniccarehospital.com"]
        assert call_json["subject"] == "Welcome Patient"
        assert call_json["text"] == "Plain text content"
        assert call_json["html"] == "<p>HTML content</p>"


def test_3_resend_plain_text_and_html_email_content():
    """3. Verifies both plain-text and HTML email content structure in send_otp_email."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_test_key_otp"

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"id": "resend_otp_123"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_resp) as mock_post:
        res = EmailService.send_otp_email(
            to_email="alice@example.com",
            otp_code="654321",
            full_name="Alice Smith",
            purpose="portal registration",
        )
        assert res["dispatched"] is True
        assert res["recipient"] == "alice@example.com"
        assert res["provider"] == "resend"

        kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        call_json = kwargs.get("payload") or mock_post.call_args[0][2]
        text_body = call_json["text"]
        html_body = call_json["html"]

        assert "Alice Smith" in text_body
        assert "654321" in text_body
        assert "10 minutes" in text_body
        assert "<!DOCTYPE html>" in html_body
        assert "654321" in html_body
        assert "portal registration" in html_body


def test_4_resend_missing_api_key_in_production(client, db_session):
    """
    4. Missing RESEND_API_KEY in production:
    - EmailService raises ResendNotConfiguredError.
    - API returns HTTP 503 Service Unavailable.
    - dev_code is NOT returned.
    """
    test_email = "prod_unconfigured_resend@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = None
    settings.SMTP_HOST = None

    with pytest.raises(ResendNotConfiguredError) as exc:
        EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")
    assert "RESEND_API_KEY is missing" in str(exc.value)

    resp = client.post(
        "/api/auth/register/send-otp",
        json={"email": test_email, "full_name": "Prod User"},
    )
    assert resp.status_code == 503
    assert "Resend email service is not configured" in resp.json()["detail"]
    assert "dev_code" not in str(resp.json())


def test_5_resend_http_401_403_auth_failure(client, db_session):
    """5. HTTP 401 and 403 provider authentication/authorization errors return HTTP 502."""
    test_email = "resend_auth_fail@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_invalid_api_key"

    # Test HTTP 401
    mock_401 = MagicMock(status_code=401)
    mock_401.json.return_value = {"statusCode": 401, "message": "API key is invalid", "name": "invalid_api_key"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_401):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Auth User"},
        )
        assert resp.status_code == 502
        assert "Resend authentication failed" in resp.json()["detail"]

    # Test HTTP 403
    mock_403 = MagicMock(status_code=403)
    mock_403.json.return_value = {"statusCode": 403, "message": "Restricted API key", "name": "restricted_api_key"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_403):
        with pytest.raises(ResendAuthenticationError) as exc:
            EmailService.send_email(to_email=test_email, subject="T", text_content="B")
        assert "Resend authentication failed" in str(exc.value)


def test_6_resend_http_422_sender_validation_failure(client, db_session):
    """6. HTTP 422 sender validation failure (unverified domain) returns HTTP 502."""
    test_email = "unverified_domain_test@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    mock_422 = MagicMock(status_code=422)
    mock_422.json.return_value = {
        "statusCode": 422,
        "message": "The domain cliniccarehospital.com is not verified. Please verify your domain in Resend.",
        "name": "validation_error",
    }

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_422):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Domain User"},
        )
        assert resp.status_code == 502
        assert "Resend validation error" in resp.json()["detail"]


def test_7_resend_http_429_rate_limit(client, db_session):
    """7. HTTP 429 provider rate limits return HTTP 502."""
    test_email = "rate_limit_test@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    mock_429 = MagicMock(status_code=429)
    mock_429.json.return_value = {
        "statusCode": 429,
        "message": "Too many requests. Please try again later.",
        "name": "rate_limit_exceeded",
    }

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_429):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Rate User"},
        )
        assert resp.status_code == 502
        assert "Resend rate limit exceeded" in resp.json()["detail"]


def test_8_resend_http_5xx_provider_error(client, db_session):
    """8. HTTP 5xx provider failures return HTTP 502."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    for code in (500, 502, 503):
        code_email = f"server_error_{code}@hospital.com"
        db_session.query(EmailVerification).filter(EmailVerification.email == code_email).delete()
        db_session.commit()

        mock_5xx = MagicMock(status_code=code)
        mock_5xx.json.return_value = {"statusCode": code, "message": "Resend internal server error"}

        with patch.object(EmailService, "_execute_resend_post", return_value=mock_5xx):
            resp = client.post(
                "/api/auth/register/send-otp",
                json={"email": code_email, "full_name": f"{code} User"},
            )
            assert resp.status_code == 502
            assert "Resend service error" in resp.json()["detail"]


def test_9_resend_network_timeout_and_connection_failure(client, db_session):
    """9. Network timeout and connection failures return HTTP 502."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    # 1. ConnectTimeout
    timeout_email = "timeout_test_net@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == timeout_email).delete()
    db_session.commit()
    with patch.object(EmailService, "_execute_resend_post", side_effect=httpx.ConnectTimeout("Connect timeout")):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": timeout_email, "full_name": "Timeout User"},
        )
        assert resp.status_code == 502
        assert "Connection to Resend API timed out" in resp.json()["detail"]

    # 2. ConnectError
    connect_email = "connect_error_net@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == connect_email).delete()
    db_session.commit()
    with patch.object(EmailService, "_execute_resend_post", side_effect=httpx.ConnectError("Connection refused")):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": connect_email, "full_name": "Connect User"},
        )
        assert resp.status_code == 502
        assert "Failed to connect to Resend HTTPS API" in resp.json()["detail"]


def test_10_resend_api_key_never_appears_in_responses_or_logs(client):
    """10. Sensitive API keys never appear in API responses, error details, or diagnostic endpoints."""
    sensitive_key = "re_super_confidential_production_key_12345"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = sensitive_key

    mock_resp = MagicMock(status_code=401)
    mock_resp.json.return_value = {"message": f"Invalid key: {sensitive_key}"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_resp):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": "audit_secret@hospital.com", "full_name": "Secret User"},
        )
        resp_text = str(resp.json())
        assert sensitive_key not in resp_text
        assert "[REDACTED_API_KEY]" in resp_text

    # Diagnostic endpoints check
    smtp_status_resp = client.get("/api/auth/smtp-status")
    assert sensitive_key not in str(smtp_status_resp.json())

    email_status_resp = client.get("/api/auth/email-status")
    assert sensitive_key not in str(email_status_resp.json())


def test_11_resend_smtp_fallback_retained(client, db_session):
    """11. SMTP fallback is safely utilized when EMAIL_PROVIDER=smtp or RESEND_API_KEY is not set."""
    test_email = "fallback_smtp_test@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    # Case A: EMAIL_PROVIDER=resend, but RESEND_API_KEY is None while SMTP is configured
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = None
    settings.SMTP_HOST = "smtp.fallback-provider.com"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "fallback_user"
    settings.SMTP_PASSWORD = "fallback_password"
    settings.SMTP_SENDER = "alerts@cliniccarehospital.com"

    assert EmailService.get_active_provider() == "smtp"
    assert EmailService.is_configured() is True

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Fallback User"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["provider"] == "smtp"
        assert resp.json()["data"]["email_dispatched"] is True


def test_12_resend_registration_otp_integration(client, db_session):
    """12. Complete registration OTP integration flow using Resend HTTPS API."""
    test_email = "reg_integration_resend@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    u = db_session.query(User).filter(User.email == test_email).first()
    if u:
        db_session.delete(u)
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_integration_test_key"

    captured_otp = None
    def mock_post(api_url, headers, payload, timeout):
        nonlocal captured_otp
        text = payload.get("text", "")
        for word in text.split():
            if len(word) == 6 and word.isdigit():
                captured_otp = word
                break
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"id": "resend_reg_flow_123"}
        return resp

    with patch.object(EmailService, "_execute_resend_post", side_effect=mock_post):
        # 1. Send Registration OTP
        resp_send = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Resend Reg Patient"},
        )
        assert resp_send.status_code == 200
        data = resp_send.json()["data"]
        assert data["email"] == test_email
        assert data["email_dispatched"] is True
        assert data["provider"] == "resend"
        assert "dev_code" not in data
        assert captured_otp is not None

        # 2. Verify Registration OTP
        resp_ver = client.post(
            "/api/auth/register/verify-otp",
            json={"email": test_email, "otp": captured_otp},
        )
        assert resp_ver.status_code == 200
        assert resp_ver.json()["data"]["verified"] is True

        # 3. Complete Registration
        resp_reg = client.post(
            "/api/auth/register",
            json={
                "email": test_email,
                "password": "Password@123",
                "full_name": "Resend Reg Patient",
                "role": "PATIENT",
                "otp": captured_otp,
            },
        )
        assert resp_reg.status_code == 201
        assert resp_reg.json()["data"]["access_token"] is not None


def test_13_resend_login_otp_integration(client, db_session):
    """13. Complete login OTP integration flow using Resend HTTPS API."""
    test_email = "login_integration_resend@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    u = db_session.query(User).filter(User.email == test_email).first()
    if not u:
        u = User(
            email=test_email,
            password_hash=get_password_hash("Password@123"),
            full_name="Resend Login Patient",
            role="PATIENT",
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_integration_test_key"

    captured_login_otp = None
    def mock_post(api_url, headers, payload, timeout):
        nonlocal captured_login_otp
        text = payload.get("text", "")
        for word in text.split():
            if len(word) == 6 and word.isdigit():
                captured_login_otp = word
                break
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"id": "resend_login_flow_123"}
        return resp

    with patch.object(EmailService, "_execute_resend_post", side_effect=mock_post):
        # 1. Send Login OTP
        resp_send = client.post("/api/auth/login/send-otp", json={"email": test_email})
        assert resp_send.status_code == 200
        data = resp_send.json()["data"]
        assert data["email"] == test_email
        assert data["email_dispatched"] is True
        assert data["provider"] == "resend"
        assert "dev_code" not in data
        assert captured_login_otp is not None

        # 2. Verify Login OTP
        resp_login = client.post(
            "/api/auth/login/verify-otp",
            json={"email": test_email, "otp": captured_login_otp},
        )
        assert resp_login.status_code == 200
        assert resp_login.json()["data"]["access_token"] is not None


def test_14_resend_production_dev_code_remains_blocked(client, db_session, monkeypatch):
    """14. Production dev_code remains strictly blocked in both register and login OTP flows."""
    monkeypatch.setenv("RENDER", "true")
    assert settings.is_production is True

    test_login_email = "prod_blocked_login_patient@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_login_email).delete()
    u = db_session.query(User).filter(User.email == test_login_email).first()
    if not u:
        u = User(
            email=test_login_email,
            password_hash=get_password_hash("Password@123"),
            full_name="Prod Patient",
            role="PATIENT",
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()

    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_key_prod_test"

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"id": "resend_dev_code_block_123"}

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_resp):
        # Registration OTP check
        reg_email = "new_prod_reg_pat@hospital.com"
        db_session.query(EmailVerification).filter(EmailVerification.email == reg_email).delete()
        db_session.commit()

        resp_reg = client.post(
            "/api/auth/register/send-otp",
            json={"email": reg_email, "full_name": "New Prod Pat"},
        )
        assert resp_reg.status_code == 200
        assert "dev_code" not in resp_reg.json()["data"]
        assert "dev_code" not in str(resp_reg.json())

        # Login OTP check
        resp_login = client.post(
            "/api/auth/login/send-otp",
            json={"email": test_login_email},
        )
        assert resp_login.status_code == 200
        assert "dev_code" not in resp_login.json()["data"]
        assert "dev_code" not in str(resp_login.json())


def test_15_status_and_health_endpoints_report_provider_configuration_correctly(client):
    """15. Status and health endpoints report provider configuration accurately."""
    # Scenario A: Resend configured
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_test_diag_key_999"
    settings.RESEND_FROM_EMAIL = "care@cliniccarehospital.com"
    settings.SMTP_HOST = None

    status_resp = client.get("/api/auth/email-status")
    assert status_resp.status_code == 200
    data = status_resp.json()["data"]
    assert data["configured"] is True
    assert data["provider"] == "resend"
    assert data["transport"] == "https"
    assert data["resend_configured"] is True
    assert data["smtp_configured"] is False
    assert data["sender"] == "care@cliniccarehospital.com"

    # Backward-compatible /api/auth/smtp-status endpoint
    legacy_resp = client.get("/api/auth/smtp-status")
    assert legacy_resp.status_code == 200
    legacy_data = legacy_resp.json()["data"]
    assert legacy_data["configured"] is True
    assert legacy_data["provider"] == "resend"
    assert legacy_data["transport"] == "https"

    # /health endpoint
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    h_data = health_resp.json()
    assert h_data["email_configured"] is True
    assert h_data["resend_configured"] is True
    assert h_data["smtp_configured"] is False
    assert h_data["email_provider"] == "resend"

    # Scenario B: SMTP configured
    settings.EMAIL_PROVIDER = "smtp"
    settings.RESEND_API_KEY = None
    settings.SMTP_HOST = "smtp.mailgun.org"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "postmaster"
    settings.SMTP_PASSWORD = "secret_password"

    health_smtp = client.get("/health")
    assert health_smtp.status_code == 200
    h_smtp_data = health_smtp.json()
    assert h_smtp_data["email_configured"] is True
    assert h_smtp_data["resend_configured"] is False
    assert h_smtp_data["smtp_configured"] is True
    assert h_smtp_data["email_provider"] == "smtp"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", "-s", __file__]))
