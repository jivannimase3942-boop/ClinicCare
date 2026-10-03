from typing import List, Optional, Any, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field


# --- Vitals Schemas ---

class VitalSignCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    consultation_id: Optional[str] = None
    temperature_celsius: Optional[float] = Field(None, ge=30.0, le=45.0)
    pulse_bpm: Optional[int] = Field(None, ge=30, le=250)
    bp_systolic: Optional[int] = Field(None, ge=50, le=300)
    bp_diastolic: Optional[int] = Field(None, ge=30, le=200)
    respiratory_rate: Optional[int] = Field(None, ge=5, le=80)
    spo2_percent: Optional[float] = Field(None, ge=50.0, le=100.0)
    weight_kg: Optional[float] = Field(None, ge=0.5, le=400.0)
    height_cm: Optional[float] = Field(None, ge=20.0, le=300.0)
    notes: Optional[str] = None


class VitalSignResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    appointment_id: Optional[str] = None
    consultation_id: Optional[str] = None
    temperature_celsius: Optional[float] = None
    pulse_bpm: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spo2_percent: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Consultation Record Schemas ---

class ConsultationRecordCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    chief_complaint: str
    history_of_present_illness: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    lifestyle_notes: Optional[str] = None
    examination_notes: Optional[str] = None
    diagnosis: str
    treatment_plan: Optional[str] = None
    investigations_ordered: Optional[str] = None
    follow_up_date: Optional[date] = None
    referral: Optional[str] = None
    clinical_notes: Optional[str] = None
    vitals: Optional[VitalSignCreate] = None


class ConsultationRecordUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    lifestyle_notes: Optional[str] = None
    examination_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    investigations_ordered: Optional[str] = None
    follow_up_date: Optional[date] = None
    referral: Optional[str] = None
    clinical_notes: Optional[str] = None


class ConsultationRecordResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    patient_name: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    appointment_id: Optional[str] = None
    status: str
    version: int
    chief_complaint: str
    history_of_present_illness: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    lifestyle_notes: Optional[str] = None
    examination_notes: Optional[str] = None
    diagnosis: str
    treatment_plan: Optional[str] = None
    investigations_ordered: Optional[str] = None
    follow_up_date: Optional[date] = None
    referral: Optional[str] = None
    clinical_notes: Optional[str] = None
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    vitals: List[VitalSignResponse] = []

    model_config = {"from_attributes": True}


# --- Clinical Document Schemas ---

class ClinicalDocumentCreate(BaseModel):
    patient_id: str
    consultation_id: Optional[str] = None
    document_type: str = Field(..., description="CONSULTATION_SUMMARY, REFERRAL_LETTER, MEDICAL_CERTIFICATE, DISCHARGE_SUMMARY, ATTACHMENT")
    title: str
    file_url: str
    file_type: str = "application/pdf"
    file_size_bytes: int = 0
    description: Optional[str] = None


class ClinicalDocumentResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    consultation_id: Optional[str] = None
    document_type: str
    title: str
    file_url: str
    file_type: str
    file_size_bytes: int
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Longitudinal Patient Timeline Item ---

class TimelineItem(BaseModel):
    event_type: str  # CONSULTATION, VITAL_SIGN, DOCUMENT, APPOINTMENT, REPORT
    event_id: str
    timestamp: datetime
    title: str
    subtitle: Optional[str] = None
    status: Optional[str] = None
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    details: Dict[str, Any] = {}


class PatientTimelineResponse(BaseModel):
    patient_id: str
    patient_name: str
    total_events: int
    events: List[TimelineItem]
