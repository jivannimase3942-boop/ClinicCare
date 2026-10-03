from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class BranchBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    address: Optional[str] = None
    city: str = Field(default="Bengaluru", max_length=100)
    state: str = Field(default="Karnataka", max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=20)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    operating_hours: str = Field(default="08:00 AM - 09:00 PM (Mon-Sat)", max_length=255)
    is_active: bool = True


class BranchCreate(BranchBase):
    organization_id: Optional[str] = None
    clinic_id: Optional[str] = None
    branch_admin_user_id: Optional[str] = None


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    operating_hours: Optional[str] = None
    branch_admin_user_id: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: str
    organization_id: str
    clinic_id: Optional[str] = None
    branch_admin_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stats: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = None
    headquarters_address: Optional[str] = None
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    headquarters_address: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    branches: List[BranchResponse] = []

    model_config = {"from_attributes": True}


class StaffInviteRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2)
    role: str = Field(..., min_length=3)
    branch_id: Optional[str] = None
    phone: Optional[str] = None
    temporary_password: Optional[str] = None
