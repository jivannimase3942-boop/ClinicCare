from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FacilityResponse(BaseModel):
    id: str
    name: str
    facility_type: str
    services: str
    address: str
    city: str
    phone: str
    emergency_hotline: str
    operating_hours: str
    is_emergency_ready: bool
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FacilityCreate(BaseModel):
    name: str
    facility_type: Optional[str] = "Multispeciality Hospital"
    services: str
    address: str
    city: str
    phone: str
    emergency_hotline: str
    operating_hours: Optional[str] = "24/7 Emergency & Inpatient"
    is_emergency_ready: Optional[bool] = True
    rating: Optional[float] = 4.8
