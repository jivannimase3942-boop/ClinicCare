from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class EscalationCreate(BaseModel):
    reason: str  # medical_question, emergency, billing, complaint, technical_issue, patient_requested_call, ai_uncertain, other
    priority: Optional[str] = "medium"  # low, medium, high, emergency
    conversation_id: Optional[str] = None
    notes: Optional[str] = None
    message: Optional[str] = None
    patient_id: Optional[str] = None
    patient_phone: Optional[str] = None


class EscalationUpdate(BaseModel):
    status: Optional[str] = None  # open, assigned, in_progress, resolved, closed
    priority: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    admin_notes: Optional[str] = None


class EscalationResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    conversation_id: Optional[str] = None
    reason: str
    message: Optional[str] = None
    status: str
    priority: str
    assigned_to_user_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

