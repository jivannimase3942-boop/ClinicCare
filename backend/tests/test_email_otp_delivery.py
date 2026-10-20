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
    ResendRestrictedRecipientError,
    ResendValidationError,
    ResendRateLimitError,
    ResendDeliveryError,
    BrevoNotConfiguredError,
    BrevoConnectionError,
    BrevoAuthenticationError,
    BrevoRestrictedSenderError,
    BrevoValidationError,
    BrevoRateLimitError,
    BrevoDeliveryError,
)
from app.models.user import User, EmailVerification
from app.core.security import get_password_hash


@pytest.fixture(autouse=True)
def restore_settings():
    """Ensure settings are restored after each test."""
    orig_env = settings.ENVIRONMENT
    orig_provider = getattr(settings, "EMAIL_PROVIDER", "resend")
    orig_brevo_key = getattr(settings, "BREVO_API_KEY", None)
    orig_brevo_sender = getattr(settings, "BREVO_SENDER_EMAIL", None)
    orig_brevo_name = getattr(settings, "BREVO_SENDER_NAME", "ClinicCare Healthcare")
    orig_resend_key = getattr(settings, "RESEND_API_KEY", None)
    orig_resend_from = getattr(settings, "RESEND_FROM_EMAIL", None)
    orig_resend_url = getattr(settings, "RESEND_API_URL", "https://api.resend.com/emails")
    orig_resend_timeout = getattr(settings, "RESEND_TIMEOUT", 10.0)
    orig_google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
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
    settings.BREVO_API_KEY = orig_brevo_key
    settings.BREVO_SENDER_EMAIL = orig_brevo_sender
    settings.BREVO_SENDER_NAME = orig_brevo_name
    settings.RESEND_API_KEY = orig_resend_key
    settings.RESEND_FROM_EMAIL = orig_resend_from
    settings.RESEND_API_URL = orig_resend_url
    settings.RESEND_TIMEOUT = orig_resend_timeout
    settings.GOOGLE_CLIENT_ID = orig_google_client_id
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
        with pytest.raises(ResendAuthenticationError) as exc:
            EmailService.send_email(to_email=test_email, subject="T", text_content="B")
        assert "Resend authentication failed" in str(exc.value)

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Auth User"},
        )
        assert resp.status_code == 502
        assert "Resend authentication failed" in resp.json()["detail"]


def test_5b_resend_http_403_restricted_recipient_domain(client, db_session):
    """5b. HTTP 403 provider restriction (sandbox test recipient or unverified domain) returns HTTP 403."""
    test_email = "external_patient_403@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    # Simulate Resend production restriction error when sending to non-owner email
    mock_403 = MagicMock(status_code=403)
    mock_403.json.return_value = {
        "statusCode": 403,
        "message": (
            "You can only send testing emails to your own email address. "
            "To send emails to other recipients, please verify a domain at resend.com/domains"
        ),
        "name": "validation_error"
    }

    with patch.object(EmailService, "_execute_resend_post", return_value=mock_403):
        # Service level
        with pytest.raises(ResendRestrictedRecipientError) as exc:
            EmailService.send_email(to_email=test_email, subject="T", text_content="B")
        assert "Resend recipient delivery restricted" in str(exc.value)

        # Registration route level
        resp_reg = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Restricted User"},
        )
        assert resp_reg.status_code == 403
        err_msg = resp_reg.json()["detail"]
        assert "Email verification delivery is restricted" in err_msg
        assert "resend.com/domains" not in err_msg  # internal URL not exposed to client


def test_6_resend_http_422_sender_validation_failure(client, db_session):
    """6. HTTP 422 sender validation failure returns HTTP 422."""
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
        with pytest.raises(ResendValidationError):
            EmailService.send_email(to_email=test_email, subject="T", text_content="B")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Domain User"},
        )
        assert resp.status_code == 422
        assert "Resend validation error" in resp.json()["detail"]


def test_7_resend_http_429_rate_limit(client, db_session):
    """7. HTTP 429 provider rate limits return HTTP 429."""
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
        with pytest.raises(ResendRateLimitError):
            EmailService.send_email(to_email=test_email, subject="T", text_content="B")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Rate User"},
        )
        assert resp.status_code == 429
        assert "Email provider rate limit reached" in resp.json()["detail"]


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


def test_16_purpose_isolation_registration_and_login_otps(client, db_session):
    """16. Purpose isolation: Registration OTP cannot be used for login; Login OTP cannot be used for registration."""
    test_email = "purpose_isolation@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    u = db_session.query(User).filter(User.email == test_email).first()
    if not u:
        u = User(
            email=test_email,
            password_hash=get_password_hash("Password@123"),
            full_name="Purpose User",
            role="PATIENT",
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "resend"
    settings.RESEND_API_KEY = "re_valid_key"

    captured_code = None
    def mock_post(api_url, headers, payload, timeout):
        nonlocal captured_code
        text = payload.get("text", "")
        for word in text.split():
            if len(word) == 6 and word.isdigit():
                captured_code = word
                break
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"id": "resend_purpose_123"}
        return resp

    with patch.object(EmailService, "_execute_resend_post", side_effect=mock_post):
        # 1. Generate registration OTP
        reg_email = "purpose_reg_only@hospital.com"
        db_session.query(EmailVerification).filter(EmailVerification.email == reg_email).delete()
        db_session.commit()

        resp_send_reg = client.post(
            "/api/auth/register/send-otp",
            json={"email": reg_email, "full_name": "Reg Purpose"},
        )
        assert resp_send_reg.status_code == 200
        reg_otp = captured_code

        # Attempt to use Registration OTP for login on registered user
        resp_bad_login = client.post(
            "/api/auth/login/verify-otp",
            json={"email": reg_email, "otp": reg_otp},
        )
        assert resp_bad_login.status_code in (400, 404)

        # 2. Generate login OTP
        resp_send_login = client.post(
            "/api/auth/login/send-otp",
            json={"email": test_email},
        )
        assert resp_send_login.status_code == 200
        login_otp = captured_code

        # Attempt to use Login OTP for registration verification
        resp_bad_reg = client.post(
            "/api/auth/register/verify-otp",
            json={"email": test_email, "otp": login_otp},
        )
        assert resp_bad_reg.status_code == 400


def test_17_concurrent_duplicate_registration_safety(client, db_session):
    """17. Concurrent duplicate registration safely rolls back and reports clean error without HTTP 500."""
    from app.services.auth_service import AuthService
    from app.schemas.auth import UserRegister

    dup_email = "concurrent_duplicate@hospital.com"
    db_session.query(User).filter(User.email == dup_email).delete()
    db_session.query(EmailVerification).filter(EmailVerification.email == dup_email).delete()
    db_session.commit()

    reg_payload = UserRegister(
        email=dup_email,
        password="Password@123",
        full_name="Duplicate Patient",
        role="PATIENT",
    )

    # First registration succeeds
    user1 = AuthService.register_user(db_session, reg_payload)
    assert user1.id is not None

    # Immediate second registration attempt raises ValueError without 500
    with pytest.raises(ValueError) as exc:
        AuthService.register_user(db_session, reg_payload)
    assert "already registered" in str(exc.value)


def test_18_login_otp_defense_against_account_enumeration(client, db_session):
    """18. Non-existent email in login OTP returns a defensive response to prevent account enumeration."""
    phantom_email = "phantom_nonexistent_user@hospital.com"
    db_session.query(User).filter(User.email == phantom_email).delete()
    db_session.commit()

    resp = client.post(
        "/api/auth/login/send-otp",
        json={"email": phantom_email},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == phantom_email
    assert "If an active account is registered" in data["message"]
    assert "dev_code" not in data


def test_19_brevo_successful_dispatch_to_any_recipient(client, db_session):
    """19. Brevo HTTPS API sends OTP to any recipient (including friends/external emails) without a custom domain."""
    test_email = "friend_external_patient@example.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_test_secret_key"
    settings.BREVO_SENDER_EMAIL = "verified_clinic@gmail.com"

    mock_resp = MagicMock(status_code=201)
    mock_resp.json.return_value = {"messageId": "<20261019.brevo.test@smtp-relay.mailin.fr>"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_resp) as mock_post:
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Friend User"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == test_email
        assert data["provider"] == "brevo"
        assert "dev_code" not in data

        # Check payload delivered to Brevo API
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs["payload"]
        assert payload["sender"]["email"] == "verified_clinic@gmail.com"
        assert payload["to"][0]["email"] == test_email


def test_20_brevo_http_401_invalid_api_key(client, db_session):
    """20. Brevo HTTP 401 returns HTTP 502 with sanitized message."""
    test_email = "brevo_auth_fail@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_invalid_key"
    settings.BREVO_SENDER_EMAIL = "sender@gmail.com"

    mock_401 = MagicMock(status_code=401)
    mock_401.json.return_value = {"code": "unauthorized", "message": "Key not found"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_401):
        with pytest.raises(BrevoAuthenticationError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Fail User"},
        )
        assert resp.status_code == 502
        assert "Brevo authentication failed" in resp.json()["detail"]


def test_21_brevo_http_403_unverified_sender(client, db_session):
    """21. Brevo HTTP 403 (sender not verified in Brevo console) returns HTTP 403."""
    test_email = "brevo_unverified_sender@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_valid_key"
    settings.BREVO_SENDER_EMAIL = "unverified_sender@gmail.com"

    mock_403 = MagicMock(status_code=403)
    mock_403.json.return_value = {"code": "permission_denied", "message": "Sender is not verified"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_403):
        with pytest.raises(BrevoRestrictedSenderError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Fail Sender"},
        )
        assert resp.status_code == 403
        assert "sender email or domain is verified" in resp.json()["detail"]


def test_22_brevo_http_400_validation_error(client, db_session):
    """22. Brevo HTTP 400 validation error returns HTTP 422."""
    test_email = "brevo_invalid_schema@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_valid_key"
    settings.BREVO_SENDER_EMAIL = "sender@gmail.com"

    mock_400 = MagicMock(status_code=400)
    mock_400.json.return_value = {"code": "invalid_parameter", "message": "Invalid email address format"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_400):
        with pytest.raises(BrevoValidationError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Bad Schema"},
        )
        assert resp.status_code == 422


def test_23_brevo_http_429_rate_limit(client, db_session):
    """23. Brevo HTTP 429 returns HTTP 429 with clear retry notice."""
    test_email = "brevo_rate_limit@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_valid_key"
    settings.BREVO_SENDER_EMAIL = "sender@gmail.com"

    mock_429 = MagicMock(status_code=429)
    mock_429.json.return_value = {"code": "too_many_requests", "message": "Daily quota exceeded"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_429):
        with pytest.raises(BrevoRateLimitError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Quota User"},
        )
        assert resp.status_code == 429
        assert "rate limit reached" in resp.json()["detail"].lower()


def test_24_brevo_http_500_provider_failure(client, db_session):
    """24. Brevo HTTP 500 returns HTTP 502 bad gateway."""
    test_email = "brevo_server_fail@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_valid_key"
    settings.BREVO_SENDER_EMAIL = "sender@gmail.com"

    mock_500 = MagicMock(status_code=500)
    mock_500.json.return_value = {"code": "internal_error", "message": "Internal server error"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_500):
        with pytest.raises(BrevoDeliveryError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Server User"},
        )
        assert resp.status_code == 502


def test_25_brevo_connection_timeout(client, db_session):
    """25. Network timeout during Brevo call raises BrevoConnectionError and HTTP 502."""
    test_email = "brevo_timeout@hospital.com"
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_valid_key"
    settings.BREVO_SENDER_EMAIL = "sender@gmail.com"

    with patch.object(EmailService, "_execute_brevo_post", side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(BrevoConnectionError):
            EmailService.send_email(to_email=test_email, subject="Test", text_content="Body")

        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Timeout User"},
        )
        assert resp.status_code == 502


def test_26_brevo_status_and_health_reporting(client):
    """26. Status endpoint reports Brevo configuration safely without leaking credentials."""
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_secret_123456789"
    settings.BREVO_SENDER_EMAIL = "safe_sender@hospital.com"

    status_data = EmailService.get_status()
    assert status_data["provider"] == "brevo"
    assert status_data["configured"] is True
    assert status_data["brevo_configured"] is True
    assert status_data["sender"] == "safe_sender@hospital.com"
    assert status_data["transport"] == "https"
    assert "xkeysib_secret" not in str(status_data)

    resp = client.get("/api/auth/email-status")
    assert resp.status_code == 200
    res_json = resp.json()["data"]
    assert res_json["provider"] == "brevo"
    assert "xkeysib_secret" not in resp.text


def test_27_google_auth_new_patient_registration(client, db_session):
    """27. Google Sign-In with verified token registers new Patient, creates record, and returns JWT."""
    from app.services.auth_service import AuthService
    google_email = "new_google_patient@hospital.com"
    db_session.query(User).filter(User.email == google_email).delete()
    db_session.commit()

    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "google_uid_123456789",
        "email": google_email,
        "email_verified": True,
        "name": "Jane Google",
        "exp": 9999999999,
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "mock_google_id_token"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data
        user_info = data["user"]
        assert user_info["email"] == google_email
        assert user_info["full_name"] == "Jane Google"
        assert user_info["role"] == "PATIENT"

        # Verify DB records
        created_user = db_session.query(User).filter(User.email == google_email).first()
        assert created_user is not None
        assert created_user.role == "PATIENT"
        assert created_user.patient_profile is not None


def test_28_google_auth_existing_user_sign_in(client, db_session):
    """28. Existing user signing in with Google resolves to existing account without duplication."""
    from app.services.auth_service import AuthService
    existing_email = "existing_google_user@hospital.com"
    db_session.query(User).filter(User.email == existing_email).delete()
    u = User(
        email=existing_email,
        password_hash=get_password_hash("Existing@123"),
        full_name="Existing Patient",
        role="PATIENT",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()

    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "google_sub_existing",
        "email": existing_email,
        "email_verified": True,
        "name": "Existing Patient",
        "exp": 9999999999,
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "mock_google_id_token"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user"]["email"] == existing_email

        # Ensure no duplicate accounts created
        count = db_session.query(User).filter(User.email == existing_email).count()
        assert count == 1


def test_29_google_auth_unverified_email_rejection(client):
    """29. Google account with unverified email is rejected with HTTP 400."""
    from app.services.auth_service import AuthService
    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "unverified_sub",
        "email": "unverified@hospital.com",
        "email_verified": False,
        "name": "Unverified User",
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "mock_unverified_token"},
        )
        assert resp.status_code == 400
        assert "verified email address" in resp.json()["detail"]


def test_30_google_auth_invalid_issuer_rejection(client):
    """30. Google token with untrusted issuer is rejected with HTTP 400."""
    from app.services.auth_service import AuthService
    mock_token_info = {
        "iss": "https://untrusted-issuer.attacker.com",
        "sub": "attacker_sub",
        "email": "attacker@hospital.com",
        "email_verified": True,
        "name": "Attacker",
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "fake_issuer_token"},
        )
        assert resp.status_code == 400
        assert "Invalid Google token issuer" in resp.json()["detail"]


def test_31_google_auth_mismatched_audience_rejection(client):
    """31. Google token with audience mismatching GOOGLE_CLIENT_ID is rejected."""
    from app.services.auth_service import AuthService
    settings.GOOGLE_CLIENT_ID = "legitimate-app-client-id.apps.googleusercontent.com"

    mock_token_info = {
        "iss": "https://accounts.google.com",
        "aud": "rogue-app-client-id.apps.googleusercontent.com",
        "sub": "rogue_sub",
        "email": "rogue@hospital.com",
        "email_verified": True,
        "name": "Rogue User",
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "mismatched_aud_token"},
        )
        assert resp.status_code == 400
        assert "audience does not match" in resp.json()["detail"]


def test_32_google_auth_expired_token_rejection(client):
    """32. Google token that has expired is rejected."""
    from app.services.auth_service import AuthService
    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "expired_sub",
        "email": "expired@hospital.com",
        "email_verified": True,
        "name": "Expired User",
        "exp": 1000000000,  # Far past timestamp
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "expired_token"},
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"]


def test_33_google_auth_disabled_account_rejection(client, db_session):
    """33. Inactive/disabled account attempting Google Sign-In is rejected."""
    from app.services.auth_service import AuthService
    disabled_email = "disabled_google_user@hospital.com"
    db_session.query(User).filter(User.email == disabled_email).delete()
    u = User(
        email=disabled_email,
        password_hash=get_password_hash("Disabled@123"),
        full_name="Disabled User",
        role="PATIENT",
        is_active=False,
    )
    db_session.add(u)
    db_session.commit()

    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "disabled_sub",
        "email": disabled_email,
        "email_verified": True,
        "name": "Disabled User",
        "exp": 9999999999,
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "disabled_user_token"},
        )
        assert resp.status_code == 400
        assert "disabled" in resp.json()["detail"]


def test_34_google_auth_role_escalation_prevention(client, db_session):
    """34. Public Google Sign-In requests cannot self-elevate to ADMIN or DOCTOR."""
    from app.services.auth_service import AuthService
    escalate_email = "hacker_escalate@hospital.com"
    db_session.query(User).filter(User.email == escalate_email).delete()
    db_session.commit()

    mock_token_info = {
        "iss": "https://accounts.google.com",
        "sub": "escalate_sub",
        "email": escalate_email,
        "email_verified": True,
        "name": "Escalate User",
        "exp": 9999999999,
    }

    with patch.object(AuthService, "_fetch_google_token_info", return_value=mock_token_info):
        resp = client.post(
            "/api/auth/google",
            json={"credential": "token", "role": "ADMIN"},
        )
        assert resp.status_code == 200
        # Role must be PATIENT
        assert resp.json()["data"]["user"]["role"] == "PATIENT"

        created_user = db_session.query(User).filter(User.email == escalate_email).first()
        assert created_user.role == "PATIENT"


def test_35_brevo_strict_provider_selection_no_smtp_fallback(client):
    """35. EMAIL_PROVIDER=brevo strictly selects Brevo HTTPS API and never falls back to Resend SMTP."""
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_provider_selection_key"
    settings.BREVO_SENDER_EMAIL = "brevo_select@hospital.com"
    settings.BREVO_SENDER_NAME = "ClinicCare Select"

    # Set Resend and SMTP settings simultaneously to simulate Render's environment
    settings.SMTP_HOST = "smtp.resend.com"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "resend"
    settings.SMTP_PASSWORD = "re_password_123"
    settings.RESEND_API_KEY = "re_resend_api_key"
    settings.RESEND_FROM_EMAIL = "onboarding@resend.dev"

    assert EmailService.get_active_provider() == "brevo"
    assert EmailService.is_configured() is True

    status_data = EmailService.get_status()
    assert status_data["provider"] == "brevo"
    assert status_data["configured"] is True
    assert status_data["sender"] == "brevo_select@hospital.com"
    assert status_data["sender_name"] == "ClinicCare Select"
    assert status_data["transport"] == "https"
    assert status_data["host"] == "api.brevo.com"
    assert status_data["port"] == 443
    assert status_data["diagnostic"] == "Brevo HTTPS API is configured and ready"

    resp = client.get("/api/auth/email-status")
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["provider"] == "brevo"
    assert res_data["sender"] == "brevo_select@hospital.com"
    assert res_data["host"] == "api.brevo.com"
    assert res_data["port"] == 443


def test_36_brevo_missing_configuration_produces_safe_diagnostics(client, db_session):
    """36. Missing or incomplete Brevo configuration produces safe diagnostics without exposing secrets."""
    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = None
    settings.BREVO_SENDER_EMAIL = None

    status_data = EmailService.get_status()
    assert status_data["provider"] == "brevo"
    assert status_data["configured"] is False
    assert status_data["brevo_configured"] is False
    assert "BREVO_API_KEY" in status_data["diagnostic"]
    assert "BREVO_SENDER_EMAIL" in status_data["diagnostic"]

    # When attempting to send registration OTP in production without configuration
    resp = client.post(
        "/api/auth/register/send-otp",
        json={"email": "unconfigured_brevo_test@hospital.com", "full_name": "Test User"},
    )
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "Brevo email service is not configured" in detail
    assert "BREVO_API_KEY" in detail


def test_37_brevo_custom_sender_name_and_email_in_payload(client, db_session):
    """37. BREVO_SENDER_NAME and BREVO_SENDER_EMAIL are propagated to Brevo API dispatch payload."""
    test_email = "brevo_sender_payload@hospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_custom_sender_key_999"
    settings.BREVO_SENDER_EMAIL = "doctor_care@cliniccarehospital.com"
    settings.BREVO_SENDER_NAME = "ClinicCare Specialist Team"

    mock_resp = MagicMock(status_code=201)
    mock_resp.json.return_value = {"messageId": "<brevo-test-msg-id-123@mailin.fr>"}

    with patch.object(EmailService, "_execute_brevo_post", return_value=mock_resp) as mock_post:
        resp = client.post(
            "/api/auth/register/send-otp",
            json={"email": test_email, "full_name": "Payload Patient"},
        )
        assert resp.status_code == 200
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs["payload"]
        assert payload["sender"]["name"] == "ClinicCare Specialist Team"
        assert payload["sender"]["email"] == "doctor_care@cliniccarehospital.com"
        assert payload["to"][0]["email"] == test_email


def test_38_health_endpoint_reports_brevo_status(client):
    """38. /health endpoint accurately reflects brevo_configured and email_provider."""
    settings.EMAIL_PROVIDER = "brevo"
    settings.BREVO_API_KEY = "xkeysib_health_check_key"
    settings.BREVO_SENDER_EMAIL = "health@cliniccarehospital.com"

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["brevo_configured"] is True
    assert data["email_configured"] is True
    assert data["email_provider"] == "brevo"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", "-s", __file__]))
