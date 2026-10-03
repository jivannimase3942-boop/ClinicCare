from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# --- Lab Test Catalog ---

class LabTestCreate(BaseModel):
    name: str
    code: str
    category: str = "BIOCHEMISTRY"
    sample_type: str = "Whole Blood"
    turnaround_hours: int = Field(24, ge=1)
    price: float = Field(..., ge=0.0)
    normal_range: Optional[str] = None
    unit: Optional[str] = None


class LabTestResponse(BaseModel):
    id: str
    clinic_id: Optional[str] = None
    name: str
    code: str
    category: str
    sample_type: str
    turnaround_hours: int
    price: float
    normal_range: Optional[str] = None
    unit: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Lab Sample ---

class LabSampleCreate(BaseModel):
    sample_type: str = "Whole Blood"


class LabSampleResponse(BaseModel):
    id: str
    lab_order_id: str
    barcode_number: str
    sample_type: str
    status: str
    rejection_reason: Optional[str] = None
    collected_at: Optional[datetime] = None
    collected_by_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Lab Result Entry ---

class LabResultEntryCreate(BaseModel):
    lab_test_id: str
    parameter_name: str
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    technician_notes: Optional[str] = None


class LabResultsSubmitRequest(BaseModel):
    results: List[LabResultEntryCreate]


class LabResultResponse(BaseModel):
    id: str
    lab_order_id: str
    lab_test_id: str
    test_name: Optional[str] = None
    parameter_name: str
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool
    technician_notes: Optional[str] = None
    tested_by_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Lab Order ---

class LabOrderCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    test_ids: List[str]
    priority: str = Field("ROUTINE", description="ROUTINE, URGENT, STAT")
    clinical_notes: Optional[str] = None


class LabReportReleaseRequest(BaseModel):
    summary_notes: Optional[str] = None


class LabReportResponse(BaseModel):
    id: str
    report_number: str
    lab_order_id: str
    clinic_id: str
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    is_validated: bool
    validated_at: Optional[datetime] = None
    validated_by_name: Optional[str] = None
    is_released: bool
    released_at: Optional[datetime] = None
    summary_notes: Optional[str] = None
    results: List[LabResultResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class LabOrderResponse(BaseModel):
    id: str
    order_number: str
    clinic_id: str
    patient_id: str
    patient_name: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    appointment_id: Optional[str] = None
    priority: str
    status: str
    clinical_notes: Optional[str] = None
    tests: List[LabTestResponse] = []
    samples: List[LabSampleResponse] = []
    results: List[LabResultResponse] = []
    report: Optional[LabReportResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
