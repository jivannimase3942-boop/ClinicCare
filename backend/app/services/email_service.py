import os
import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, Any, Optional

import httpx
from app.core.config import settings


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class EmailNotConfiguredError(EmailServiceError):
    """Raised when email credentials/keys are missing in an environment that requires them."""
    pass


class EmailConnectionError(EmailServiceError):
    """Raised when network connection, timeout, or DNS resolution fails."""
    pass


class EmailAuthenticationError(EmailServiceError):
    """Raised when email provider authentication or authorization is rejected."""
    pass


class EmailDeliveryError(EmailServiceError):
    """Raised when message transmission or recipient is rejected by email provider."""
    pass


# Specific SMTP exception subclasses for backward compatibility
class SMTPNotConfiguredError(EmailNotConfiguredError):
    """Raised when SMTP credentials/host are missing in an environment that requires them."""
    pass


class SMTPConnectionError(EmailConnectionError):
    """Raised when connecting or establishing TLS to the SMTP server fails."""
    pass


class SMTPAuthenticationError(EmailAuthenticationError):
    """Raised when SMTP authentication is rejected by the provider."""
    pass


class SMTPDeliveryError(EmailDeliveryError):
    """Raised when message transmission or recipient is rejected by SMTP server."""
    pass


# Specific Resend HTTPS API exception subclasses
class ResendNotConfiguredError(EmailNotConfiguredError):
    """Raised when Resend API key is missing in an environment that requires it."""
    pass


class ResendConnectionError(EmailConnectionError):
    """Raised when network connection or timeout to Resend API occurs."""
    pass


class ResendAuthenticationError(EmailAuthenticationError):
    """Raised when Resend API rejects credentials with HTTP 401/403."""
    pass


class ResendDeliveryError(EmailDeliveryError):
    """Raised when Resend rejects message payload (HTTP 422, 429, 5xx)."""
    pass


class EmailService:
    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Sanitizes text to prevent API keys or passwords from appearing in exception messages or logs."""
        if not text:
            return ""
        clean = str(text)
        if getattr(settings, "RESEND_API_KEY", None) and len(settings.RESEND_API_KEY) > 4:
            clean = clean.replace(settings.RESEND_API_KEY, "[REDACTED_API_KEY]")
        if getattr(settings, "SMTP_PASSWORD", None) and len(settings.SMTP_PASSWORD) > 4:
            clean = clean.replace(settings.SMTP_PASSWORD, "[REDACTED_PASSWORD]")
        return clean

    @staticmethod
    def is_smtp_configured() -> bool:
        """Checks if all necessary SMTP credentials and host are provided."""
        return bool(
            getattr(settings, "SMTP_HOST", None)
            and getattr(settings, "SMTP_USER", None)
            and getattr(settings, "SMTP_PASSWORD", None)
        )

    @staticmethod
    def is_resend_configured() -> bool:
        """Checks if Resend API key is configured."""
        key = getattr(settings, "RESEND_API_KEY", None)
        return bool(key and str(key).strip())

    @staticmethod
    def get_active_provider() -> str:
        """
        Resolves the active email transport provider.
        Supports 'resend' (HTTPS API) and 'smtp' (traditional SMTP).
        If provider is 'resend' but RESEND_API_KEY is missing while SMTP is configured,
        falls back to SMTP for backward compatibility.
        """
        pref = (getattr(settings, "EMAIL_PROVIDER", None) or "resend").strip().lower()
        if pref == "smtp":
            return "smtp"
        if pref == "resend":
            if EmailService.is_resend_configured():
                return "resend"
            if EmailService.is_smtp_configured():
                return "smtp"
            return "resend"
        return pref

    @staticmethod
    def is_configured() -> bool:
        """Checks if the active email provider is fully configured with required credentials."""
        provider = EmailService.get_active_provider()
        if provider == "resend":
            return EmailService.is_resend_configured()
        elif provider == "smtp":
            return EmailService.is_smtp_configured()
        return False

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """
        Returns safe diagnostic status without exposing secret API keys or passwords.
        Maintains backward compatibility with legacy SMTP keys while exposing provider-neutral diagnostics.
        """
        configured = EmailService.is_configured()
        provider = EmailService.get_active_provider()
        use_ssl = bool(getattr(settings, "SMTP_USE_SSL", False) or getattr(settings, "SMTP_PORT", 587) == 465)
        use_tls = bool(getattr(settings, "SMTP_USE_TLS", True) and not use_ssl)

        sender = (
            getattr(settings, "RESEND_FROM_EMAIL", None)
            or getattr(settings, "SMTP_SENDER", None)
            or getattr(settings, "SMTP_USER", None)
            or "alerts@cliniccarehospital.com"
        )

        transport = "https" if provider == "resend" else ("ssl" if use_ssl else ("tls" if use_tls else "plain"))

        return {
            "configured": configured,
            "provider": provider,
            "sender": sender,
            "transport": transport,
            "email_configured": configured,
            "smtp_configured": EmailService.is_smtp_configured(),
            "resend_configured": EmailService.is_resend_configured(),
            "host": getattr(settings, "SMTP_HOST", None) or None,
            "port": getattr(settings, "SMTP_PORT", 587),
            "use_tls": use_tls,
            "use_ssl": use_ssl,
        }

    @staticmethod
    def _execute_resend_post(
        api_url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        """Executes the HTTP POST request to the Resend API."""
        with httpx.Client(timeout=timeout) as client:
            return client.post(api_url, headers=headers, json=payload)

    @staticmethod
    def _send_via_resend(
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Dispatches email via Resend HTTPS API using httpx.
        Enforces strict timeouts, safe error handling, and no secret leakage.
        """
        normalized_recipient = to_email.strip().lower()
        if not EmailService.is_resend_configured():
            if settings.is_production:
                raise ResendNotConfiguredError(
                    "Resend email service is not configured on this server. "
                    "Required environment variable RESEND_API_KEY is missing."
                )
            print(f"[ClinicCare Email] Notice: Resend API key unconfigured in {settings.ENVIRONMENT} mode. Skipping dispatch to {normalized_recipient}.")
            return False

        # Determine sender header
        raw_sender = from_email or getattr(settings, "RESEND_FROM_EMAIL", None) or getattr(settings, "SMTP_SENDER", None) or "alerts@cliniccarehospital.com"
        raw_sender = str(raw_sender).strip()
        sender_name = from_name or getattr(settings, "SMTP_SENDER_NAME", "ClinicCare Healthcare")

        if "<" in raw_sender and ">" in raw_sender:
            sender_header = raw_sender
        elif sender_name:
            sender_header = f"{sender_name} <{raw_sender}>"
        else:
            sender_header = raw_sender

        api_url = getattr(settings, "RESEND_API_URL", "https://api.resend.com/emails")
        timeout = float(getattr(settings, "RESEND_TIMEOUT", 10.0))
        api_key = settings.RESEND_API_KEY.strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ClinicCare-Healthcare/1.0",
        }

        payload: Dict[str, Any] = {
            "from": sender_header,
            "to": [normalized_recipient],
            "subject": subject,
            "text": text_content,
        }
        if html_content:
            payload["html"] = html_content

        try:
            resp = EmailService._execute_resend_post(api_url=api_url, headers=headers, payload=payload, timeout=timeout)
        except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ResendConnectionError(
                f"Connection to Resend API timed out after {timeout}s: {EmailService._sanitize_text(str(e))}"
            )
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise ResendConnectionError(
                f"Failed to connect to Resend HTTPS API: {EmailService._sanitize_text(str(e))}"
            )
        except Exception as e:
            raise ResendConnectionError(
                f"Network error during Resend email dispatch: {EmailService._sanitize_text(str(e))}"
            )

        if 200 <= resp.status_code < 300:
            print(f"[ClinicCare Email] Successfully dispatched email via Resend to {normalized_recipient}")
            return True

        # Extract safe error details from response body without logging sensitive headers or payload
        err_msg = ""
        try:
            err_json = resp.json()
            if isinstance(err_json, dict):
                err_msg = err_json.get("message") or err_json.get("error") or str(err_json)
            else:
                err_msg = resp.text[:200]
        except Exception:
            err_msg = resp.text[:200]
        err_msg = EmailService._sanitize_text(err_msg)

        if resp.status_code in (401, 403):
            raise ResendAuthenticationError(
                f"Resend authentication failed (HTTP {resp.status_code}): {err_msg or 'Invalid API key or unauthorized permission'}"
            )
        elif resp.status_code == 422:
            raise ResendDeliveryError(
                f"Resend validation error (HTTP 422): {err_msg or 'Invalid sender domain or recipient address'}"
            )
        elif resp.status_code == 429:
            raise ResendDeliveryError(
                f"Resend rate limit exceeded (HTTP 429): {err_msg or 'Too many requests; rate limit reached'}"
            )
        elif 500 <= resp.status_code < 600:
            raise ResendDeliveryError(
                f"Resend service error (HTTP {resp.status_code}): {err_msg or 'Provider server failure'}"
            )
        else:
            raise ResendDeliveryError(
                f"Resend rejected email dispatch with HTTP {resp.status_code}: {err_msg}"
            )

    @staticmethod
    def _send_via_smtp(
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Sends an email via SMTP with RFC-compliant headers and HTML+Plaintext multipart support.
        Maintained as backward-compatible fallback for environments supporting outbound SMTP.
        """
        normalized_recipient = to_email.strip().lower()
        if not EmailService.is_smtp_configured():
            if settings.is_production:
                raise SMTPNotConfiguredError(
                    "SMTP email service is not configured on this server. "
                    "Required environment variables (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) are missing."
                )
            print(f"[ClinicCare Email] Notice: SMTP unconfigured in {settings.ENVIRONMENT} mode. Skipping dispatch to {normalized_recipient}.")
            return False

        sender_email = from_email or settings.SMTP_SENDER or settings.SMTP_USER
        sender_name = from_name or getattr(settings, "SMTP_SENDER_NAME", "ClinicCare Healthcare")
        sender_header = f"{sender_name} <{sender_email}>"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_header
        msg["To"] = normalized_recipient
        msg["Date"] = formatdate(localtime=True)

        domain = "cliniccarehospital.com"
        if settings.SMTP_HOST and "." in settings.SMTP_HOST:
            domain = settings.SMTP_HOST
        msg["Message-ID"] = make_msgid(domain=domain)

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        timeout = getattr(settings, "SMTP_TIMEOUT", 10)
        use_ssl = bool(getattr(settings, "SMTP_USE_SSL", False) or settings.SMTP_PORT == 465)
        use_tls = bool(getattr(settings, "SMTP_USE_TLS", True) and not use_ssl)

        try:
            if use_ssl:
                ssl_context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ssl_context, timeout=timeout) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as server:
                    if use_tls:
                        server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            print(f"[ClinicCare Email] Successfully dispatched email via SMTP to {normalized_recipient}")
            return True

        except (socket.timeout, socket.gaierror, ConnectionRefusedError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            raise SMTPConnectionError(
                f"Failed to connect to SMTP server '{settings.SMTP_HOST}:{settings.SMTP_PORT}': {EmailService._sanitize_text(str(e))}"
            )
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(
                f"SMTP authentication failed for account '{settings.SMTP_USER}': {EmailService._sanitize_text(str(e))}"
            )
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError) as e:
            raise SMTPDeliveryError(
                f"SMTP mail provider rejected delivery: {EmailService._sanitize_text(str(e))}"
            )
        except smtplib.SMTPException as e:
            raise SMTPDeliveryError(
                f"SMTP error during message dispatch: {EmailService._sanitize_text(str(e))}"
            )
        except Exception as e:
            raise SMTPDeliveryError(
                f"Unexpected error during email dispatch: {EmailService._sanitize_text(str(e))}"
            )

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Dispatches an email using the active provider (Resend HTTPS API or SMTP).
        Raises specific, safe exception on connection, auth, or delivery failures.
        """
        normalized_recipient = to_email.strip().lower()
        if not normalized_recipient:
            raise ValueError("Recipient email address cannot be empty")

        provider = EmailService.get_active_provider()
        if provider == "resend":
            return EmailService._send_via_resend(
                to_email=normalized_recipient,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name,
            )
        elif provider == "smtp":
            return EmailService._send_via_smtp(
                to_email=normalized_recipient,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name,
            )
        else:
            raise EmailDeliveryError(f"Unsupported email provider: {provider}")

    @staticmethod
    def send_otp_email(
        to_email: str,
        otp_code: str,
        full_name: Optional[str] = None,
        purpose: str = "account registration",
    ) -> Dict[str, Any]:
        """
        Sends a high-deliverability branded OTP verification email with both plain text and HTML
        via the active email provider (Resend HTTPS API or SMTP).
        """
        display_name = full_name or "Patient"
        subject = f"Your ClinicCare Verification Code: {otp_code}"

        text_content = (
            f"Hello {display_name},\n\n"
            f"Your ClinicCare 6-digit verification code is: {otp_code}\n\n"
            f"This code will expire in 10 minutes.\n"
            f"If you did not request this verification code, please disregard this email.\n\n"
            f"Thank you,\n"
            f"ClinicCare Multispeciality Healthcare\n"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ClinicCare Verification</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <div style="background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%); padding: 32px 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">ClinicCare Healthcare</h1>
      <p style="color: rgba(255, 255, 255, 0.85); margin: 6px 0 0 0; font-size: 13px;">Secure Portal Verification</p>
    </div>
    <div style="padding: 32px 28px;">
      <p style="font-size: 15px; margin: 0 0 16px 0; color: #334155;">Hello <strong>{display_name}</strong>,</p>
      <p style="font-size: 14px; margin: 0 0 24px 0; color: #475569; line-height: 1.5;">
        Please use the following 6-digit verification code to complete your {purpose}:
      </p>
      <div style="background-color: #f0fdf4; border: 1px dashed #22c55e; border-radius: 12px; padding: 20px; text-align: center; margin: 0 0 24px 0;">
        <span style="font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #15803d;">{otp_code}</span>
        <p style="margin: 8px 0 0 0; font-size: 12px; color: #166534;">Valid for 10 minutes</p>
      </div>
      <p style="font-size: 12px; color: #64748b; margin: 0 0 16px 0; line-height: 1.5;">
        If you did not initiate this request, no action is needed. Your account remains secure.
      </p>
      <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0 16px 0;" />
      <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
        ClinicCare Multispeciality Hospital &bull; Automated Healthcare System
      </p>
    </div>
  </div>
</body>
</html>"""

        dispatched = EmailService.send_email(
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )

        provider = EmailService.get_active_provider()
        is_conf = EmailService.is_configured()

        return {
            "dispatched": dispatched,
            "recipient": to_email.strip().lower(),
            "provider": provider,
            "email_configured": is_conf,
            "smtp_configured": is_conf,
        }


email_service = EmailService()
