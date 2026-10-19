import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, Any, Optional
from app.core.config import settings


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class SMTPNotConfiguredError(EmailServiceError):
    """Raised when SMTP credentials/host are missing in an environment that requires them."""
    pass


class SMTPConnectionError(EmailServiceError):
    """Raised when connecting or establishing TLS to the SMTP server fails."""
    pass


class SMTPAuthenticationError(EmailServiceError):
    """Raised when SMTP authentication is rejected by the provider."""
    pass


class SMTPDeliveryError(EmailServiceError):
    """Raised when message transmission or recipient is rejected by SMTP server."""
    pass


class EmailService:
    @staticmethod
    def is_configured() -> bool:
        """Checks if all necessary SMTP credentials are provided."""
        return bool(
            settings.SMTP_HOST
            and settings.SMTP_USER
            and settings.SMTP_PASSWORD
        )

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Returns safe SMTP diagnostic status without exposing credentials."""
        configured = EmailService.is_configured()
        use_ssl = bool(getattr(settings, "SMTP_USE_SSL", False) or settings.SMTP_PORT == 465)
        use_tls = bool(getattr(settings, "SMTP_USE_TLS", True) and not use_ssl)
        sender = settings.SMTP_SENDER or settings.SMTP_USER or "alerts@cliniccarehospital.com"
        
        return {
            "configured": configured,
            "host": settings.SMTP_HOST or None,
            "port": settings.SMTP_PORT,
            "sender": sender,
            "use_tls": use_tls,
            "use_ssl": use_ssl,
        }

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
        Sends an email via SMTP with RFC-compliant headers and HTML+Plaintext multipart support.
        Raises specific exceptions on connection, auth, or delivery failures.
        """
        normalized_recipient = to_email.strip().lower()
        if not normalized_recipient:
            raise ValueError("Recipient email address cannot be empty")

        if not EmailService.is_configured():
            if settings.is_production:
                raise SMTPNotConfiguredError(
                    "SMTP email service is not configured on this server. "
                    "Required environment variables (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) are missing."
                )
            # In non-production development environments, log safely without failing
            print(f"[ClinicCare Email] Notice: SMTP unconfigured in {settings.ENVIRONMENT} mode. Skipping dispatch to {normalized_recipient}.")
            return False

        # Sender determination: prefer explicit from_email, then settings.SMTP_SENDER, then settings.SMTP_USER
        sender_email = from_email or settings.SMTP_SENDER or settings.SMTP_USER
        sender_name = from_name or getattr(settings, "SMTP_SENDER_NAME", "ClinicCare Healthcare")
        sender_header = f"{sender_name} <{sender_email}>"

        # Construct RFC-compliant multipart message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_header
        msg["To"] = normalized_recipient
        msg["Date"] = formatdate(localtime=True)
        
        # Safe domain for Message-ID
        domain = "cliniccarehospital.com"
        if settings.SMTP_HOST and "." in settings.SMTP_HOST:
            domain = settings.SMTP_HOST
        msg["Message-ID"] = make_msgid(domain=domain)

        # Plain text alternative
        msg.attach(MIMEText(text_content, "plain", "utf-8"))

        # HTML alternative
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

            print(f"[ClinicCare Email] Successfully dispatched email to {normalized_recipient}")
            return True

        except (socket.timeout, socket.gaierror, ConnectionRefusedError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            raise SMTPConnectionError(
                f"Failed to connect to SMTP server '{settings.SMTP_HOST}:{settings.SMTP_PORT}': {str(e)}"
            )
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(
                f"SMTP authentication failed for account '{settings.SMTP_USER}': {str(e)}"
            )
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError) as e:
            raise SMTPDeliveryError(
                f"SMTP mail provider rejected delivery: {str(e)}"
            )
        except smtplib.SMTPException as e:
            raise SMTPDeliveryError(
                f"SMTP error during message dispatch: {str(e)}"
            )
        except Exception as e:
            raise SMTPDeliveryError(
                f"Unexpected error during email dispatch: {str(e)}"
            )

    @staticmethod
    def send_otp_email(
        to_email: str,
        otp_code: str,
        full_name: Optional[str] = None,
        purpose: str = "account registration",
    ) -> Dict[str, Any]:
        """
        Sends a high-deliverability branded OTP verification email with both plain text and HTML.
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

        return {
            "dispatched": dispatched,
            "recipient": to_email.strip().lower(),
            "smtp_configured": EmailService.is_configured(),
        }


email_service = EmailService()
