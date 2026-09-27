from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class VoiceCallCreate(BaseModel):
    phone: Optional[str] = None
    reason: str
    urgency: Optional[str] = None
    patient_id: Optional[str] = None


class VoiceCallUpdateStatus(BaseModel):
    status: str
    notes: Optional[str] = None


class VoiceCallResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    phone: Optional[str] = None
    reason: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
