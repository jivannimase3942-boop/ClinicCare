from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: date
    appointment_time: str = Field(..., description="Format HH:MM e.g. 09:30")
    appointment_type: Optional[str] = Field("NEW_CONSULTATION", description="NEW_CONSULTATION, FOLLOW_UP, PROCEDURE, TELECONSULTATION, EMERGENCY, HOME_VISIT")
    reason: Optional[str] = None
    notes: Optional[str] = None
    patient_id: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_name: Optional[str] = None
    is_walk_in: Optional[bool] = False
    parent_appointment_id: Optional[str] = None


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


class AppointmentQueueUpdate(BaseModel):
    queue_status: str = Field(..., description="WAITING, CALLED, IN_CONSULTATION, COMPLETED, SKIPPED, CANCELLED")
    notes: Optional[str] = None


class WalkInCreate(BaseModel):
    doctor_id: str
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None
    reason: Optional[str] = None
    appointment_type: Optional[str] = "NEW_CONSULTATION"


class DoctorLeaveCreate(BaseModel):
    doctor_id: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class DoctorLeaveResponse(BaseModel):
    id: str
    clinic_id: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    start_date: date
    end_date: date
    reason: Optional[str] = None
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WaitlistCreate(BaseModel):
    doctor_id: str
    desired_date: date
    preferred_time_range: Optional[str] = Field(None, description="e.g. Morning, Afternoon, 10:00-12:00")
    notes: Optional[str] = None


class WaitlistResponse(BaseModel):
    id: str
    clinic_id: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    desired_date: date
    preferred_time_range: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DoctorScheduleUpdate(BaseModel):
    available_days: Optional[str] = None
    available_hours_start: Optional[str] = None
    available_hours_end: Optional[str] = None
    break_start_time: Optional[str] = None
    break_end_time: Optional[str] = None
    slot_duration_minutes: Optional[int] = None
    max_daily_patients: Optional[int] = None


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
    appointment_type: Optional[str] = "NEW_CONSULTATION"
    token_number: Optional[str] = None
    queue_status: Optional[str] = "NOT_QUEUED"
    checked_in_at: Optional[datetime] = None
    consultation_started_at: Optional[datetime] = None
    consultation_ended_at: Optional[datetime] = None
    is_walk_in: Optional[bool] = False
    parent_appointment_id: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    cancelled_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SlotCheckRequest(BaseModel):
    doctor_id: str
    slot_date: date

