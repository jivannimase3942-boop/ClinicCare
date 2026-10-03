from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# Sessions
class UserSessionResponse(BaseModel):
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    is_active: bool
    last_activity_at: datetime
    expires_at: datetime
    created_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


# Security Events
class SecurityEventResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    event_type: str
    severity: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Password Change
class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


# Staff Status Update
class StaffStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None


# Consent
class PatientConsentCreate(BaseModel):
    consent_type: str = Field(..., description="COMMUNICATION_CONSENT, TELEMEDICINE_CONSENT, DATA_SHARING_CONSENT, etc.")
    purpose: str = Field(..., min_length=3, max_length=255)
    source: str = Field(default="PATIENT_PORTAL")
    expires_at: Optional[datetime] = None


class PatientConsentWithdraw(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class PatientConsentResponse(BaseModel):
    id: str
    patient_id: str
    clinic_id: Optional[str] = None
    consent_type: str
    purpose: str
    status: str
    source: str
    ip_address: Optional[str] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Privacy DSAR Requests
class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(..., description="DATA_EXPORT or DATA_DELETION")
    reason: Optional[str] = None


class PrivacyRequestProcess(BaseModel):
    status: str = Field(..., description="COMPLETED or REJECTED")
    retention_note: Optional[str] = None


class PrivacyRequestResponse(BaseModel):
    id: str
    patient_id: str
    request_type: str
    status: str
    reason: Optional[str] = None
    retention_note: Optional[str] = None
    export_payload: Optional[Dict[str, Any]] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# MFA
class MFASetupRequest(BaseModel):
    enable: bool
    method: str = Field(default="EMAIL_OTP")


class MFAResponse(BaseModel):
    is_enabled: bool
    method: str
    configured: bool
    last_verified_at: Optional[datetime] = None
