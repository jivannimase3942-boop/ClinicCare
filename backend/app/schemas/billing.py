from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class InvoiceItemCreate(BaseModel):
    item_type: str = Field("CONSULTATION", description="CONSULTATION, PROCEDURE, LAB_TEST, MEDICINE, SERVICE")
    description: str
    quantity: int = Field(1, ge=1)
    unit_price: float = Field(..., ge=0.0)


class InvoiceItemResponse(BaseModel):
    id: str
    item_type: str
    description: str
    quantity: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    doctor_id: Optional[str] = None
    items: List[InvoiceItemCreate]
    discount_amount: float = Field(0.0, ge=0.0)
    tax_rate_percent: float = Field(0.0, ge=0.0)
    notes: Optional[str] = None


class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0.0)
    payment_method: str = Field("CASH", description="CASH, UPI, CARD, ONLINE_GATEWAY, BANK_TRANSFER")
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    payment_method: str
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundCreate(BaseModel):
    amount: float = Field(..., gt=0.0)
    reason: str


class RefundResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    clinic_id: str
    clinic_name: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_address: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    appointment_id: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    subtotal: float
    discount_amount: float
    tax_rate_percent: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    balance_due: float
    status: str
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    items: List[InvoiceItemResponse] = []
    payments: List[PaymentResponse] = []
    refunds: List[RefundResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RevenueSummaryResponse(BaseModel):
    total_revenue: float = 0.0
    today_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    consultation_revenue: float
    procedure_revenue: float
    payment_methods: Dict[str, float]
    pending_dues: float
    total_refunds: float
    invoice_count: int
