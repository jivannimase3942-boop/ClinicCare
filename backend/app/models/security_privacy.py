import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class UserSession(Base):
    """
    Tracks active authentication sessions per user for enterprise session management,
    instant token revocation, and device awareness.
    """
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_jti = Column(String(64), unique=True, nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_activity_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", backref="sessions")


class SecurityEvent(Base):
    """
    Comprehensive audit for high-risk security actions:
    Logins, Logouts, Password Changes, Role Changes, Suspicious Logins, MFA events.
    """
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    # Types: LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, LOGOUT_ALL, PASSWORD_CHANGE, ROLE_CHANGE,
    # STAFF_ACTIVATION, STAFF_DEACTIVATION, SUSPICIOUS_LOGIN_ATTEMPT, MFA_CHALLENGE, CONSENT_GRANTED, CONSENT_REVOKED
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, HIGH, CRITICAL
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User")
    clinic = relationship("Clinic")


class PatientConsent(Base):
    """
    Explicit, auditable patient consent records across multiple healthcare purposes.
    Consent is never assumed merely because a user created an account.
    """
    __tablename__ = "patient_consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True, index=True)
    consent_type = Column(String(100), nullable=False, index=True)
    # Types: COMMUNICATION_CONSENT, TELEMEDICINE_CONSENT, DATA_SHARING_CONSENT, DOCUMENT_SHARING_CONSENT
    purpose = Column(String(255), nullable=False)
    status = Column(String(50), default="GRANTED", nullable=False, index=True)  # GRANTED, REVOKED, EXPIRED
    source = Column(String(100), default="PATIENT_PORTAL", nullable=False)  # PATIENT_PORTAL, IN_CLINIC, VERBAL, SMS_OTP
    ip_address = Column(String(100), nullable=True)
    granted_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient", backref="consents")
    clinic = relationship("Clinic")


class PrivacyRequest(Base):
    """
    Formal Data Subject Access Requests (DSAR) under Indian DPDPA & global standards:
    Data Export, Data Deletion, Retention Notes.
    Medical records cannot be blindly deleted due to statutory retention mandates.
    """
    __tablename__ = "privacy_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True)  # DATA_EXPORT, DATA_DELETION
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, REJECTED
    reason = Column(Text, nullable=True)
    retention_note = Column(Text, nullable=True)
    export_payload = Column(Text, nullable=True)  # JSON dump of exported data
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient", backref="privacy_requests")
    processor = relationship("User", foreign_keys=[processed_by_user_id])


class MFAConfig(Base):
    """
    Multi-Factor Authentication configuration and readiness.
    Accurately indicates if MFA is active or configured.
    """
    __tablename__ = "mfa_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    method = Column(String(50), default="EMAIL_OTP", nullable=False)  # EMAIL_OTP, TOTP, SMS
    secret = Column(String(255), nullable=True)
    backup_codes = Column(Text, nullable=True)  # Comma-separated or JSON
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", backref="mfa_config", uselist=False)
