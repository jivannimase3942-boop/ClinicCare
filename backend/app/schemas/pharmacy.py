from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


# --- Supplier Schemas ---

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    dl_number: Optional[str] = None
    address: Optional[str] = None


class SupplierResponse(BaseModel):
    id: str
    clinic_id: str
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    dl_number: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Stock Batch Schemas ---

class StockBatchCreate(BaseModel):
    medicine_id: str
    supplier_id: Optional[str] = None
    batch_number: str
    expiry_date: date
    purchase_price: float = Field(0.0, ge=0.0)
    mrp: float = Field(0.0, ge=0.0)
    sale_price: float = Field(0.0, ge=0.0)
    initial_quantity: int = Field(..., ge=1)
    reorder_threshold: int = Field(20, ge=0)


class StockBatchResponse(BaseModel):
    id: str
    clinic_id: str
    medicine_id: str
    medicine_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage_form: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    batch_number: str
    expiry_date: date
    purchase_price: float
    mrp: float
    sale_price: float
    initial_quantity: int
    current_quantity: int
    reorder_threshold: int
    is_active: bool
    is_expired: bool = False
    is_near_expiry: bool = False
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Stock Transaction Schemas ---

class StockAdjustmentCreate(BaseModel):
    batch_id: str
    transaction_type: str = Field(..., description="PURCHASE, SALE, ISSUE, RETURN, DAMAGE, ADJUSTMENT, TRANSFER")
    quantity: int = Field(..., description="Quantity delta. Positive for inbound, negative for outbound.")
    reason: Optional[str] = None
    unit_price: Optional[float] = None


class StockTransactionResponse(BaseModel):
    id: str
    clinic_id: str
    batch_id: str
    batch_number: Optional[str] = None
    medicine_id: str
    medicine_name: Optional[str] = None
    transaction_type: str
    quantity: int
    balance_after: int
    unit_price: float
    invoice_id: Optional[str] = None
    prescription_id: Optional[str] = None
    reason: Optional[str] = None
    actor_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Alerts & Summaries ---

class StockAlertItemResponse(BaseModel):
    batch_id: str
    batch_number: str
    medicine_id: str
    medicine_name: str
    expiry_date: date
    current_quantity: int
    reorder_threshold: int
    alert_type: str  # EXPIRED, NEAR_EXPIRY, LOW_STOCK
    severity: str    # HIGH, MEDIUM, LOW
    message: str


# --- Pharmacy Dispense & Billing Linkage ---

class PharmacyDispenseItem(BaseModel):
    batch_id: str
    quantity: int = Field(..., ge=1)


class PharmacyDispenseRequest(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    prescription_id: Optional[str] = None
    items: List[PharmacyDispenseItem]
    payment_method: str = "CASH"  # CASH, UPI, CARD, ONLINE_GATEWAY
    notes: Optional[str] = None


class PharmacyDispenseResponse(BaseModel):
    invoice_id: str
    invoice_number: str
    total_amount: float
    status: str
    items_dispensed: int
    message: str
