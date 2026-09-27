from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AmbulanceResponse(BaseModel):
    id: str
    vehicle_number: str
    model: str
    ambulance_type: str
    status: str  # available, busy, offline, maintenance
    base_station: str
    current_location: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    paramedic_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AmbulanceCreate(BaseModel):
    vehicle_number: str
    model: str
    ambulance_type: Optional[str] = "Basic Life Support (BLS)"
    base_station: Optional[str] = "ClinicCare Main Campus"
    current_location: Optional[str] = "Main Base, Bay 1"
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    paramedic_name: Optional[str] = None


class AmbulanceStatusUpdate(BaseModel):
    status: str
    current_location: Optional[str] = None


class AmbulanceRequestCreate(BaseModel):
    patient_id: Optional[str] = None
    requester_name: str
    requester_phone: str
    pickup_address: str
    destination_facility: Optional[str] = "ClinicCare Multispeciality Hospital"
    emergency_priority: Optional[str] = "high"  # low, medium, high, critical
    notes: Optional[str] = None


class AmbulanceRequestStatusUpdate(BaseModel):
    status: str  # requested, assigned, en_route, arrived, completed, cancelled
    ambulance_id: Optional[str] = None
    notes: Optional[str] = None


class AmbulanceAssignPayload(BaseModel):
    ambulance_id: str
    notes: Optional[str] = None


class AmbulanceRequestResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    ambulance_id: Optional[str] = None
    ambulance_vehicle_number: Optional[str] = None
    ambulance_model: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    requester_name: str
    requester_phone: str
    pickup_address: str
    destination_facility: str
    emergency_priority: str
    status: str
    notes: Optional[str] = None
    is_simulated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
