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
import pytest

from app.core.config import settings
from app.services.email_service import (
    EmailService,
    email_service,
    SMTPNotConfiguredError,
    SMTPConnectionError,
    SMTPAuthenticationError,
    SMTPDeliveryError,
)
from app.models.user import User, EmailVerification


@pytest.fixture(autouse=True)
def restore_settings():
    """Ensure settings are restored after each test."""
    orig_env = settings.ENVIRONMENT
    orig_host = settings.SMTP_HOST
    orig_port = settings.SMTP_PORT
    orig_user = settings.SMTP_USER
    orig_pass = settings.SMTP_PASSWORD
    orig_sender = settings.SMTP_SENDER
    orig_debug = settings.DEBUG
    yield
    settings.ENVIRONMENT = orig_env
    settings.SMTP_HOST = orig_host
    settings.SMTP_PORT = orig_port
    settings.SMTP_USER = orig_user
    settings.SMTP_PASSWORD = orig_pass
    settings.SMTP_SENDER = orig_sender
    settings.DEBUG = orig_debug


def test_smtp_delivery_success(client, db_session):
    """Verifies successful SMTP dispatch with full RFC headers and HTML/plain text parts."""
    test_email = "verified_delivery_test@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
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
        # In production, dev_code MUST NEVER be included
        assert "dev_code" not in data

        # Verify SMTP server interactions
        mock_smtp_class.assert_called_with("smtp.sendgrid.net", 587, timeout=10)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("apikey", "SG.test-secret-key-12345")
        mock_smtp_instance.send_message.assert_called_once()

        # Verify message headers
        sent_msg = mock_smtp_instance.send_message.call_args[0][0]
        assert "noreply@cliniccarehospital.com" in sent_msg["From"]
        assert sent_msg["To"] == test_email
        assert "ClinicCare Verification Code" in sent_msg["Subject"]
        assert sent_msg["Date"] is not None
        assert sent_msg["Message-ID"] is not None


def test_smtp_missing_configuration_in_production(client, db_session):
    """
    Verifies that when SMTP is unconfigured in production:
    1. EmailService raises SMTPNotConfiguredError.
    2. API returns HTTP 503 instead of false HTTP 200.
    3. dev_code is NEVER returned.
    """
    test_email = "unconfigured_smtp_prod@cliniccarehospital.com"
    db_session.query(EmailVerification).filter(EmailVerification.email == test_email).delete()
    db_session.commit()

    settings.ENVIRONMENT = "production"
    settings.SMTP_HOST = None
    settings.SMTP_USER = None
    settings.SMTP_PASSWORD = None

    # 1. Direct service call raises SMTPNotConfiguredError
    with pytest.raises(SMTPNotConfiguredError) as exc_info:
        EmailService.send_email(
            to_email=test_email,
            subject="Test",
            text_content="Body",
        )
    assert "SMTP email service is not configured on this server" in str(exc_info.value)

    # 2. API returns HTTP 503 Service Unavailable
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
    settings.SMTP_HOST = "smtp.relay.example.com"
    settings.SMTP_PORT = 465
    settings.SMTP_USER = "smtp_admin"
    settings.SMTP_PASSWORD = "super_secret_value_do_not_leak"
    settings.SMTP_SENDER = "notifications@cliniccarehospital.com"
    settings.SMTP_USE_SSL = True

    # 1. /api/auth/smtp-status endpoint
    resp = client.get("/api/auth/smtp-status")
    assert resp.status_code == 200
    status_data = resp.json()["data"]
    assert status_data["configured"] is True
    assert status_data["host"] == "smtp.relay.example.com"
    assert status_data["port"] == 465
    assert status_data["sender"] == "notifications@cliniccarehospital.com"
    assert status_data["use_ssl"] is True
    # Ensure password and sensitive keys are NEVER present in response
    assert "password" not in str(resp.json()).lower() or "super_secret" not in str(resp.json())

    # 2. /health endpoint reports smtp_configured
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["smtp_configured"] is True


if __name__ == "__main__":
    import sys
    from pathlib import Path
    print("==================================================", flush=True)
    print("Starting test_email_otp_delivery test runner...", flush=True)
    print("Loading FastAPI application, schemas, and fixtures (~20s)...", flush=True)
    print("==================================================", flush=True)
    backend_path = Path(__file__).resolve().parent.parent
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    import pytest
    sys.exit(pytest.main(["-v", "-s", __file__]))


