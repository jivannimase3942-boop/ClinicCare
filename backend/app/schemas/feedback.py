from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    appointment_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    comment: Optional[str] = None
    patient_id: Optional[str] = None
    phone: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
