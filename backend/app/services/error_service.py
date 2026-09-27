import json
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.error_log import ErrorLog


class ErrorService:
    @staticmethod
    def build_alert_message(
        service_name: str,
        error_level: str,
        message: str,
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Builds structured alert message details for monitoring/email alerting."""
        subject = f"[{error_level}] Alert: {service_name} error on {endpoint or 'system'}"
        body = (
            f"Hospital AI Automation System Alert\n"
            f"====================================\n"
            f"Severity: {error_level}\n"
            f"Service: {service_name}\n"
            f"Endpoint: {endpoint or 'N/A'}\n"
            f"Message: {message}\n"
            f"Context: {json.dumps(context, indent=2) if context else 'None'}\n\n"
            f"Stack Trace:\n{stack_trace or 'No stack trace provided'}\n"
        )
        return {"subject": subject, "body": body}

    @staticmethod
    def send_error_alert_email(subject: str, body: str) -> Dict[str, Any]:
        """Sends error alert email via SMTP if configured, or reports controlled config state."""
        if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
            return {
                "status": "unconfigured",
                "message": "SMTP email credentials not configured. Error alert captured in database error_logs.",
                "recipient": settings.ALERT_EMAIL_TO,
                "subject": subject
            }
        
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_SENDER
            msg["To"] = settings.ALERT_EMAIL_TO
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return {"status": "sent", "recipient": settings.ALERT_EMAIL_TO}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def log_error(
        db: Session,
        message: str,
        service_name: str = "backend",
        error_level: str = "ERROR",
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ErrorLog]:
        try:
            context_str = json.dumps(context) if context else None
            log_entry = ErrorLog(
                service_name=service_name,
                error_level=error_level,
                message=message,
                stack_trace=stack_trace,
                endpoint=endpoint,
                context_json=context_str,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            # Build alert message and dispatch if ERROR or CRITICAL
            if error_level in ["ERROR", "CRITICAL"]:
                alert = ErrorService.build_alert_message(
                    service_name=service_name,
                    error_level=error_level,
                    message=message,
                    stack_trace=stack_trace,
                    endpoint=endpoint,
                    context=context,
                )
                ErrorService.send_error_alert_email(alert["subject"], alert["body"])

            return log_entry
        except Exception as e:
            db.rollback()
            print(f"Failed to log error to database: {e}")
            return None


error_service = ErrorService()

