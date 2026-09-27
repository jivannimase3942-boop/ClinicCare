from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FollowUpReminderResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    appointment_id: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    reminder_type: str
    scheduled_for: datetime
    title: str
    message: str
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowUpReminderCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    doctor_id: Optional[str] = None
    reminder_type: Optional[str] = "upcoming_appointment"
    scheduled_for: datetime
    title: str
    message: str
    channel: Optional[str] = "WhatsApp/SMS (Demo)"
