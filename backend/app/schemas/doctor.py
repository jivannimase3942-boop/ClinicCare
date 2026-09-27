from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: str = "Activity"
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DoctorSlotResponse(BaseModel):
    id: str
    doctor_id: str
    slot_date: date
    start_time: str
    end_time: str
    is_booked: bool

    model_config = {"from_attributes": True}


class DoctorBase(BaseModel):
    department_id: str
    specialization: str
    qualification: str
    experience_years: int = 0
    consultation_fee: float = 0.00
    location: str = "Main OPD, Room 101"
    available_days: str = "Monday,Tuesday,Wednesday,Thursday,Friday"
    available_hours_start: str = "09:00"
    available_hours_end: str = "17:00"
    slot_duration_minutes: int = 30
    profile_image: Optional[str] = None
    is_active: bool = True


class DoctorCreate(DoctorBase):
    user_id: str


class DoctorUpdate(BaseModel):
    department_id: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    location: Optional[str] = None
    available_days: Optional[str] = None
    available_hours_start: Optional[str] = None
    available_hours_end: Optional[str] = None
    slot_duration_minutes: Optional[int] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    department_id: str
    department_name: Optional[str] = None
    specialization: str
    qualification: str
    experience_years: int
    consultation_fee: float
    location: str
    available_days: str
    available_hours_start: str
    available_hours_end: str
    slot_duration_minutes: int
    profile_image: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
