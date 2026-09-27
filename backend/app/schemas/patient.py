from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class PatientProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class VisitHistoryResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    appointment_id: Optional[str] = None
    visit_date: date
    visit_type: str
    visit_status: str
    vitals_summary: Optional[str] = None
    administrative_notes: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitHistoryCreate(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    department_id: Optional[str] = None
    appointment_id: Optional[str] = None
    visit_date: date
    visit_type: Optional[str] = "OPD Consultation"
    visit_status: Optional[str] = "completed"
    vitals_summary: Optional[str] = None
    administrative_notes: Optional[str] = None
    follow_up_instructions: Optional[str] = None
