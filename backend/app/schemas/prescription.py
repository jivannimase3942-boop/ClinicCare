from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


# --- Medicine Master Schemas ---

class MedicineCreate(BaseModel):
    brand_name: str
    generic_name: str
    strength: str
    dosage_form: str = "TABLET"
    manufacturer: Optional[str] = None
    category: str = "GENERAL"
    hsn_code: Optional[str] = "3004"
    gst_rate_percent: float = Field(12.0, ge=0.0, le=28.0)
    unit_price: float = Field(0.0, ge=0.0)


class MedicineResponse(BaseModel):
    id: str
    clinic_id: Optional[str] = None
    brand_name: str
    generic_name: str
    strength: str
    dosage_form: str
    manufacturer: Optional[str] = None
    category: str
    hsn_code: Optional[str] = None
    gst_rate_percent: float
    unit_price: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Prescription Items ---

class PrescriptionItemCreate(BaseModel):
    medicine_id: Optional[str] = None
    medicine_name: str
    generic_name: Optional[str] = None
    dosage_form: str = "TABLET"
    strength: Optional[str] = None
    dosage: str = "1 tablet"
    frequency: str = "1-0-1 (Twice daily)"
    duration: str = "5 days"
    route: str = "ORAL"
    instructions: str = "After food"
    quantity: int = Field(10, ge=1)


class PrescriptionItemResponse(BaseModel):
    id: str
    prescription_id: str
    medicine_id: Optional[str] = None
    medicine_name: str
    generic_name: Optional[str] = None
    dosage_form: str
    strength: Optional[str] = None
    dosage: str
    frequency: str
    duration: str
    route: str
    instructions: str
    quantity: int

    model_config = {"from_attributes": True}


# --- Prescription ---

class PrescriptionCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    consultation_id: Optional[str] = None
    diagnosis_summary: str
    general_advice: Optional[str] = None
    diet_lifestyle_notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    items: List[PrescriptionItemCreate] = []


class PrescriptionResponse(BaseModel):
    id: str
    prescription_number: str
    clinic_id: str
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_gender: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    doctor_qualification: Optional[str] = None
    appointment_id: Optional[str] = None
    consultation_id: Optional[str] = None
    status: str
    diagnosis_summary: str
    general_advice: Optional[str] = None
    diet_lifestyle_notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    items: List[PrescriptionItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
