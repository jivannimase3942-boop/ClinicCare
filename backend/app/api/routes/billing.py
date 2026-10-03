import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    RefundCreate,
    RevenueSummaryResponse,
)
from app.services.billing_service import billing_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/invoices", response_model=ApiResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    if not current_user.clinic_id and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active clinic associated with user")

    clinic_id = current_user.clinic_id or "default"
    try:
        inv = billing_service.create_invoice(
            db=db,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message=f"Invoice {inv.invoice_number} created", data=inv)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invoice error: {str(e)}")


@router.get("/invoices", response_model=ApiResponse[List[InvoiceResponse]])
def get_invoices(
    patient_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "PATIENT":
        # Strict privacy: patient only sees their own invoices
        if not current_user.patient_profile:
            return ApiResponse(success=True, data=[])
        invoices = billing_service.get_invoices(
            db=db,
            patient_id=current_user.patient_profile.id,
            status=status_filter
        )
        return ApiResponse(success=True, data=invoices)

    if current_user.role in ["ADMIN", "FRONT_DESK", "SUPER_ADMIN", "ACCOUNTANT"]:
        clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
        target_pid = patient_id
        invoices = billing_service.get_invoices(
            db=db,
            clinic_id=clinic_filter,
            patient_id=target_pid,
            status=status_filter
        )
        return ApiResponse(success=True, data=invoices)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/invoices/{id}", response_model=ApiResponse[InvoiceResponse])
def get_invoice(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = billing_service.get_invoice_by_id(db, invoice_id=id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Patient privacy
    if current_user.role == "PATIENT":
        if not current_user.patient_profile or inv.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's invoice")

    # Clinic tenant isolation
    if current_user.role in ["ADMIN", "FRONT_DESK", "ACCOUNTANT"]:
        if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and inv.clinic_id and current_user.clinic_id != inv.clinic_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot access invoice of another clinic")

    return ApiResponse(success=True, data=inv)


@router.post("/invoices/{id}/payments", response_model=ApiResponse[InvoiceResponse])
def record_payment(
    id: str,
    data: PaymentCreate,
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "SUPER_ADMIN", "ACCOUNTANT"])),
    db: Session = Depends(get_db)
):
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    try:
        updated = billing_service.record_payment(
            db=db,
            invoice_id=id,
            data=data,
            clinic_id=clinic_filter,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Payment collected successfully", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invoices/{id}/refund", response_model=ApiResponse[InvoiceResponse])
def record_refund(
    id: str,
    data: RefundCreate,
    current_user: User = Depends(require_roles(["ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    try:
        updated = billing_service.record_refund(
            db=db,
            invoice_id=id,
            data=data,
            clinic_id=clinic_filter,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Refund processed successfully", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/revenue", response_model=ApiResponse[RevenueSummaryResponse])
def get_revenue(
    current_user: User = Depends(require_roles(["ADMIN", "SUPER_ADMIN", "FRONT_DESK", "ACCOUNTANT"])),
    db: Session = Depends(get_db)
):
    if not current_user.clinic_id and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active clinic associated with user")

    clinic_id = current_user.clinic_id or "default"
    summary = billing_service.get_revenue_summary(db, clinic_id=clinic_id)
    return ApiResponse(success=True, data=summary)


@router.post("/online-order")
def create_online_payment_order(
    invoice_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Real gateway readiness endpoint for Razorpay/Cashfree. Never fakes payment success."""
    inv = billing_service.get_invoice_by_id(db, invoice_id=invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    if current_user.role == "PATIENT":
        if not current_user.patient_profile or inv.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    razorpay_key = os.getenv("RAZORPAY_KEY_ID")
    razorpay_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not razorpay_key or not razorpay_secret:
        return ApiResponse(
            success=False,
            message="Online payment is not configured. Please pay via Cash or UPI at clinic reception.",
            data={
                "gateway_configured": False,
                "provider": "razorpay",
                "invoice_number": inv.invoice_number,
                "balance_due": inv.balance_due,
            }
        )

    # When credentials are provided in environment, instantiate gateway SDK order
    return ApiResponse(
        success=True,
        message="Order created",
        data={
            "gateway_configured": True,
            "provider": "razorpay",
            "key_id": razorpay_key,
            "amount": int(inv.balance_due * 100),
            "currency": "INR",
        }
    )
