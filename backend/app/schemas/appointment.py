from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: date
    appointment_time: str = Field(..., description="Format HH:MM e.g. 09:30")
    reason: Optional[str] = None
    notes: Optional[str] = None
    patient_id: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_name: Optional[str] = None


class AppointmentReschedule(BaseModel):
    new_date: date
    new_time: str = Field(..., description="Format HH:MM e.g. 10:00")
    reason: Optional[str] = None


class AppointmentCancel(BaseModel):
    cancelled_reason: Optional[str] = "Cancelled by patient"
    cancellation_reason: Optional[str] = None

    def get_reason(self) -> str:
        return self.cancellation_reason or self.cancelled_reason or "Cancelled by patient"


class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None



class AppointmentResponse(BaseModel):
    id: str
    clinic_id: Optional[str] = None
    clinic_name: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    appointment_date: date
    appointment_time: str
    status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    cancelled_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SlotCheckRequest(BaseModel):
    doctor_id: str
    slot_date: date
