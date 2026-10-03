from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.prescription import (
    MedicineCreate,
    MedicineResponse,
    PrescriptionCreate,
    PrescriptionResponse,
)
from app.services.prescription_service import prescription_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, Doctor, Patient


router = APIRouter(prefix="/prescriptions", tags=["Digital Prescriptions & Medicine Master"])


@router.get("/medicines", response_model=ApiResponse[List[MedicineResponse]])
def list_medicines(
    search: Optional[str] = Query(None, description="Search medicine brand or generic name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists medicines from the active formulary master."""
    clinic_id = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    meds = prescription_service.list_medicines(db=db, clinic_id=clinic_id, search=search)
    return ApiResponse(success=True, data=meds)


@router.post("/medicines", response_model=ApiResponse[MedicineResponse], status_code=status.HTTP_201_CREATED)
def create_medicine(
    data: MedicineCreate,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Adds a new medicine to the formulary master."""
    med = prescription_service.create_medicine(
        db=db,
        clinic_id=current_user.clinic_id,
        data=data,
        actor_id=current_user.id
    )
    return ApiResponse(success=True, message="Medicine added to master", data=med)


@router.post("", response_model=ApiResponse[PrescriptionResponse], status_code=status.HTTP_201_CREATED)
def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """
    Physician creates a digital prescription draft.
    Human physician supervision is mandatory. AI cannot autonomously issue prescriptions.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor profile not found for active user")

    clinic_id = current_user.clinic_id or "default"
    try:
        rx = prescription_service.create_prescription(
            db=db,
            clinic_id=clinic_id,
            doctor_id=doctor.id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Prescription draft created", data=rx)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/finalize", response_model=ApiResponse[PrescriptionResponse])
def finalize_prescription(
    id: str,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """
    Physician finalizes and issues the digital prescription with digital signature block.
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        rx = prescription_service.finalize_prescription(
            db=db,
            prescription_id=id,
            clinic_id=clinic_id,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Prescription finalized and issued", data=rx)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}", response_model=ApiResponse[PrescriptionResponse])
def get_prescription(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches a prescription. Patients can only view finalized prescriptions issued to them."""
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    rx = prescription_service.get_prescription(db, prescription_id=id, clinic_id=clinic_filter)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    if current_user.role == "PATIENT":
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != rx.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if not rx.is_finalized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Prescription draft is pending physician signature")

    return ApiResponse(success=True, data=rx)


@router.get("/patient/{patient_id}", response_model=ApiResponse[List[PrescriptionResponse]])
def list_patient_prescriptions(
    patient_id: str,
    finalized_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists prescriptions for a patient. Patient role can only view their own finalized prescriptions."""
    is_patient = current_user.role == "PATIENT"
    if is_patient:
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's prescriptions")
        finalized_only = True

    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    rx_list = prescription_service.list_patient_prescriptions(
        db=db,
        patient_id=patient_id,
        clinic_id=clinic_filter,
        finalized_only=finalized_only
    )
    return ApiResponse(success=True, data=rx_list)
