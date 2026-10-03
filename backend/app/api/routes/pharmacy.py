from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.pharmacy import (
    SupplierCreate,
    SupplierResponse,
    StockBatchCreate,
    StockBatchResponse,
    StockAdjustmentCreate,
    StockTransactionResponse,
    StockAlertItemResponse,
    PharmacyDispenseRequest,
    PharmacyDispenseResponse,
)
from app.services.pharmacy_service import pharmacy_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User


router = APIRouter(prefix="/pharmacy", tags=["Pharmacy & Inventory Foundation"])


# --- Supplier Management ---

@router.post("/suppliers", response_model=ApiResponse[SupplierResponse], status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Registers a new pharmaceutical supplier / distributor."""
    clinic_id = current_user.clinic_id or "default"
    sup = pharmacy_service.create_supplier(
        db=db,
        clinic_id=clinic_id,
        data=data,
        actor_id=current_user.id
    )
    return ApiResponse(success=True, message="Supplier registered successfully", data=sup)


@router.get("/suppliers", response_model=ApiResponse[List[SupplierResponse]])
def list_suppliers(
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Lists registered suppliers for the clinic."""
    clinic_id = current_user.clinic_id or "default"
    suppliers = pharmacy_service.list_suppliers(db=db, clinic_id=clinic_id)
    return ApiResponse(success=True, data=suppliers)


# --- Batch & Stock Management ---

@router.post("/batches", response_model=ApiResponse[StockBatchResponse], status_code=status.HTTP_201_CREATED)
def create_stock_batch(
    data: StockBatchCreate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """
    Registers a new batch of medicines with expiry date, cost, MRP, and initial stock.
    Automatically logs an inbound PURCHASE transaction.
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        batch = pharmacy_service.create_batch(
            db=db,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Stock batch added to inventory", data=batch)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/batches", response_model=ApiResponse[List[StockBatchResponse]])
def list_stock_batches(
    medicine_id: Optional[str] = Query(None, description="Filter by medicine ID"),
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Lists inventory batches sorted by earliest expiry date (FEFO)."""
    clinic_id = current_user.clinic_id or "default"
    batches = pharmacy_service.list_batches(
        db=db,
        clinic_id=clinic_id,
        medicine_id=medicine_id
    )
    return ApiResponse(success=True, data=batches)


@router.get("/alerts", response_model=ApiResponse[List[StockAlertItemResponse]])
def get_inventory_alerts(
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Returns low stock, near-expiry, and expired inventory alerts."""
    clinic_id = current_user.clinic_id or "default"
    alerts = pharmacy_service.get_stock_alerts(db=db, clinic_id=clinic_id)
    return ApiResponse(success=True, data=alerts)


# --- Auditable Stock Adjustments & Ledger ---

@router.post("/adjustments", response_model=ApiResponse[StockBatchResponse])
def adjust_stock(
    data: StockAdjustmentCreate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR"])),
    db: Session = Depends(get_db)
):
    """
    Applies an auditable manual stock adjustment (RETURN, DAMAGE, ADJUSTMENT, TRANSFER).
    Requires authorized human supervision.
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        updated_batch = pharmacy_service.adjust_stock(
            db=db,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Stock adjusted and logged to ledger", data=updated_batch)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/transactions", response_model=ApiResponse[List[StockTransactionResponse]])
def list_stock_transactions(
    batch_id: Optional[str] = Query(None),
    medicine_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR"])),
    db: Session = Depends(get_db)
):
    """Auditable stock movement ledger."""
    clinic_id = current_user.clinic_id or "default"
    txs = pharmacy_service.list_transactions(
        db=db,
        clinic_id=clinic_id,
        batch_id=batch_id,
        medicine_id=medicine_id
    )
    return ApiResponse(success=True, data=txs)


# --- Dispense & Billing Engine Integration ---

@router.post("/dispense", response_model=ApiResponse[PharmacyDispenseResponse], status_code=status.HTTP_201_CREATED)
def dispense_and_bill(
    data: PharmacyDispenseRequest,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """
    Dispenses medicines to patient:
    - Validates FEFO / non-expired stock
    - Deducts batch inventory
    - Records auditable SALE stock transaction
    - Automatically links to the existing Billing Invoice & Item engine
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        resp = pharmacy_service.dispense_and_bill(
            db=db,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message=resp.message, data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
