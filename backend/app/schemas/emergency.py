from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class EmergencyRequestCreate(BaseModel):
    patient_id: Optional[str] = None
    caller_name: str
    caller_phone: str
    location: str
    emergency_type: str  # Cardiac, Trauma, Respiratory, Stroke, Severe Bleeding, General Emergency
    priority: Optional[str] = "critical"  # medium, high, critical
    notes: Optional[str] = None
    requires_ambulance: Optional[bool] = True


class EmergencyRequestResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    caller_name: str
    caller_phone: str
    location: str
    emergency_type: str
    priority: str
    status: str  # open, dispatched, in_progress, resolved, closed
    ambulance_id: Optional[str] = None
    ambulance_vehicle_number: Optional[str] = None
    assigned_staff_id: Optional[str] = None
    assigned_staff_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmergencyStatsResponse(BaseModel):
    total_emergencies: int
    critical_active: int
    dispatched_ambulances: int
    resolved_today: int
    average_response_minutes: float

