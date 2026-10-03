from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.lab import (
    LabTestCreate,
    LabTestResponse,
    LabOrderCreate,
    LabOrderResponse,
    LabResultsSubmitRequest,
    LabReportReleaseRequest,
    LabReportResponse,
)
from app.services.lab_service import lab_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, Doctor, Patient


router = APIRouter(prefix="/lab", tags=["Laboratory Workflow & Diagnostics"])


@router.get("/tests", response_model=ApiResponse[List[LabTestResponse]])
def list_lab_tests(
    category: Optional[str] = Query(None, description="Filter by test category"),
    search: Optional[str] = Query(None, description="Search by test name or code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists available lab tests from the active catalog."""
    clinic_id = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    tests = lab_service.list_lab_tests(db=db, clinic_id=clinic_id, category=category, search=search)
    return ApiResponse(success=True, data=tests)


@router.post("/tests", response_model=ApiResponse[LabTestResponse], status_code=status.HTTP_201_CREATED)
def create_lab_test(
    data: LabTestCreate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR"])),
    db: Session = Depends(get_db)
):
    """Adds a new test to the clinic diagnostic catalog."""
    test = lab_service.create_lab_test(
        db=db,
        clinic_id=current_user.clinic_id,
        data=data,
        actor_id=current_user.id
    )
    return ApiResponse(success=True, message="Lab test added to catalog", data=test)


@router.post("/orders", response_model=ApiResponse[LabOrderResponse], status_code=status.HTTP_201_CREATED)
def create_lab_order(
    data: LabOrderCreate,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """
    Physician places a laboratory diagnostic order with barcode-ready sample tracking.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor profile not found for active user")

    clinic_id = current_user.clinic_id or "default"
    try:
        order = lab_service.create_lab_order(
            db=db,
            clinic_id=clinic_id,
            doctor_id=doctor.id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Laboratory order placed successfully", data=order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/orders", response_model=ApiResponse[List[LabOrderResponse]])
def list_lab_orders(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Lists laboratory orders for the clinic."""
    clinic_id = current_user.clinic_id or "default"
    orders = lab_service.list_orders(
        db=db,
        clinic_id=clinic_id,
        patient_id=patient_id,
        status=status_filter
    )
    return ApiResponse(success=True, data=orders)


@router.get("/orders/{id}", response_model=ApiResponse[LabOrderResponse])
def get_lab_order(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches a lab order with samples, results, and release status."""
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    order = lab_service.get_lab_order(db=db, order_id=id, clinic_id=clinic_filter)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")

    if current_user.role == "PATIENT":
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != order.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ApiResponse(success=True, data=order)


@router.post("/samples/{sample_id}/collect", response_model=ApiResponse[LabOrderResponse])
def collect_sample(
    sample_id: str,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Marks a sample as collected with timestamp and operator verification."""
    clinic_id = current_user.clinic_id or "default"
    try:
        updated_order = lab_service.collect_sample(
            db=db,
            sample_id=sample_id,
            clinic_id=clinic_id,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Sample collected successfully", data=updated_order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{id}/results", response_model=ApiResponse[LabOrderResponse])
def enter_results(
    id: str,
    data: LabResultsSubmitRequest,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Records diagnostic parameters and values for a lab order."""
    clinic_id = current_user.clinic_id or "default"
    try:
        updated_order = lab_service.enter_results(
            db=db,
            order_id=id,
            clinic_id=clinic_id,
            results_data=data.results,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Lab results recorded", data=updated_order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{id}/release", response_model=ApiResponse[LabReportResponse])
def release_lab_report(
    id: str,
    data: LabReportReleaseRequest,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Validates and releases the formal laboratory diagnostic report.
    Synchronizes with patient report repository.
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        report = lab_service.validate_and_release_report(
            db=db,
            order_id=id,
            clinic_id=clinic_id,
            summary_notes=data.summary_notes,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Lab report validated and released", data=report)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/patient/{patient_id}", response_model=ApiResponse[List[LabOrderResponse]])
def list_patient_orders(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists lab orders for a patient with authorization checks."""
    if current_user.role == "PATIENT":
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's lab orders")

    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    orders = lab_service.list_orders(
        db=db,
        clinic_id=clinic_filter or "default",
        patient_id=patient_id
    )
    return ApiResponse(success=True, data=orders)
