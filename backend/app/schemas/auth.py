from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


class SendOtpRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    role: str = "PATIENT"  # Default PATIENT
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    otp: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class PatientProfileResponse(BaseModel):
    id: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

    model_config = {"from_attributes": True}


class DoctorProfileResponse(BaseModel):
    id: str
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
    profile_image: Optional[str] = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    patient_profile: Optional[PatientProfileResponse] = None
    doctor_profile: Optional[DoctorProfileResponse] = None

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
