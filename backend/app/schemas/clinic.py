from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class ClinicBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = "Bengaluru"
    state: Optional[str] = "Karnataka"
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    operating_hours: Optional[str] = "09:00 AM - 08:00 PM (Monday - Saturday)"
    consultation_fee_default: Optional[float] = 500.00


class ClinicOnboardRequest(ClinicBase):
    # Initial departments & clinical services
    departments: Optional[List[str]] = Field(
        default_factory=lambda: [
            "General Medicine",
            "Pediatrics",
            "Cardiology",
            "Orthopedics",
            "Gynecology",
        ]
    )
    services: Optional[List[str]] = Field(
        default_factory=lambda: [
            "OPD Consultation",
            "Emergency Triage",
            "Preventive Health Checkup",
            "Diagnostic Sample Collection",
        ]
    )
    # Primary clinic administrator credentials
    admin_name: str = Field(..., min_length=2)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)
    admin_phone: Optional[str] = None

    # Optional primary practitioner details
    doctor_name: Optional[str] = None
    doctor_email: Optional[EmailStr] = None
    doctor_specialization: Optional[str] = None
    doctor_qualification: Optional[str] = None
    doctor_fee: Optional[float] = None


class ClinicResponse(ClinicBase):
    id: str
    slug: str
    is_active: bool
    settings_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClinicPublicResponse(BaseModel):
    id: str
    name: str
    slug: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    operating_hours: str
    consultation_fee_default: float
    departments: List[str] = []

    model_config = {"from_attributes": True}


class ClinicUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    operating_hours: Optional[str] = None
    consultation_fee_default: Optional[float] = None
    settings_json: Optional[str] = None


class ClinicOnboardResponse(BaseModel):
    clinic: ClinicResponse
    admin_user: Dict[str, Any]
    doctor_user: Optional[Dict[str, Any]] = None
    portal_url: str
    message: str
