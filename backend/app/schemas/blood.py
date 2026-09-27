from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class BloodInventoryItem(BaseModel):
    id: str
    blood_bank_id: str
    blood_group: str
    units_available: int
    status: str
    last_updated: datetime

    model_config = {"from_attributes": True}


class BloodBankResponse(BaseModel):
    id: str
    name: str
    city: str
    address: str
    phone: str
    email: Optional[str] = None
    operating_hours: str
    is_verified: bool
    inventory: List[BloodInventoryItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BloodGroupSearchResult(BaseModel):
    blood_bank_id: str
    blood_bank_name: str
    city: str
    address: str
    phone: str
    blood_group: str
    units_available: int
    status: str
    last_updated: datetime
    operating_hours: str


class BloodInventoryUpdate(BaseModel):
    units_available: int
    status: Optional[str] = None


class BloodRequestCreate(BaseModel):
    patient_id: Optional[str] = None
    patient_name: str
    blood_group: str  # A+, A-, B+, B-, AB+, AB-, O+, O-
    units_required: int = 1
    hospital_clinic_name: str
    location: str
    contact_phone: str
    urgency: Optional[str] = "urgent"  # normal, urgent, critical
    additional_info: Optional[str] = None


class BloodRequestStatusUpdate(BaseModel):
    status: str  # submitted, searching, match_found, fulfilled, cancelled
    admin_notes: Optional[str] = None
    matched_blood_bank_id: Optional[str] = None
    matched_bank_name: Optional[str] = None


class BloodRequestMatchPayload(BaseModel):
    blood_bank_id: str
    notes: Optional[str] = None


class BloodRequestResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    patient_name: str
    blood_group: str
    units_required: int
    hospital_clinic_name: str
    location: str
    contact_phone: str
    urgency: str
    additional_info: Optional[str] = None
    status: str
    matched_blood_bank_id: Optional[str] = None
    matched_bank_name: Optional[str] = None
    admin_notes: Optional[str] = None
    is_simulated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

