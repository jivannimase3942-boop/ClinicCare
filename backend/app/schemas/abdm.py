from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ABDMStatusResponse(BaseModel):
    integration_configured: bool
    gateway_url: str
    facility_id: Optional[str] = None
    supported_hi_types: List[str] = Field(default_factory=lambda: [
        "OPConsultation", "Prescription", "DiagnosticReport", "DischargeSummary"
    ])
    sandbox_mode: bool = True
    notice: str


class ABHAProfileResponse(BaseModel):
    id: str
    patient_id: str
    abha_number: Optional[str] = None
    abha_address: Optional[str] = None
    verification_status: str
    kyc_verified: bool
    auth_methods: List[str] = Field(default_factory=list)
    linked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ABHAAuthInitiateRequest(BaseModel):
    auth_mode: str = Field(..., description="Authentication mode: AADHAAR_OTP, MOBILE_OTP, DEMOGRAPHICS")
    identifier: str = Field(..., description="14-digit ABHA number, mobile number, or Aadhaar reference")


class ABHAAuthInitiateResponse(BaseModel):
    integration_configured: bool
    transaction_id: Optional[str] = None
    status: str
    message: str
    supported_methods: List[str] = Field(default_factory=lambda: ["AADHAAR_OTP", "MOBILE_OTP"])


class ABDMConsentCreateRequest(BaseModel):
    patient_id: str
    purpose_code: str = Field("CAREMGT", description="CAREMGT, BTG, PUBHLTH, RESRCH")
    purpose_text: str = Field("Care Management", description="Human-readable consent purpose")
    hi_types: List[str] = Field(default_factory=lambda: ["OPConsultation", "Prescription", "DiagnosticReport"])
    facility_hfr_id: Optional[str] = None
    date_range_from: Optional[datetime] = None
    date_range_to: Optional[datetime] = None
    data_erase_at: Optional[datetime] = None


class ABDMConsentResponse(BaseModel):
    id: str
    consent_request_id: str
    consent_id: Optional[str] = None
    patient_id: str
    requester_user_id: Optional[str] = None
    facility_hfr_id: Optional[str] = None
    purpose_code: str
    purpose_text: str
    hi_types: List[str]
    status: str
    date_range_from: Optional[datetime] = None
    date_range_to: Optional[datetime] = None
    data_erase_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacilityRegistryCreateRequest(BaseModel):
    branch_id: Optional[str] = None
    clinic_id: Optional[str] = None
    facility_name: str
    hfr_id: Optional[str] = None
    facility_type: str = "HOSPITAL"
    system_of_medicine: str = "ALLOPATHY"
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    pincode: Optional[str] = None


class FacilityRegistryResponse(BaseModel):
    id: str
    branch_id: Optional[str] = None
    clinic_id: Optional[str] = None
    facility_name: str
    hfr_id: Optional[str] = None
    facility_type: str
    system_of_medicine: str
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    pincode: Optional[str] = None
    verification_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfessionalRegistryCreateRequest(BaseModel):
    doctor_id: str
    hpr_id: Optional[str] = None
    registration_number: Optional[str] = None
    state_medical_council: Optional[str] = None
    year_of_registration: Optional[str] = None
    system_of_medicine: str = "ALLOPATHY"


class ProfessionalRegistryResponse(BaseModel):
    id: str
    doctor_id: str
    hpr_id: Optional[str] = None
    registration_number: Optional[str] = None
    state_medical_council: Optional[str] = None
    year_of_registration: Optional[str] = None
    system_of_medicine: str
    verification_status: str
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
