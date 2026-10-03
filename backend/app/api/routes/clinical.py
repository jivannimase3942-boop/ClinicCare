from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.clinical import (
    VitalSignCreate,
    VitalSignResponse,
    ConsultationRecordCreate,
    ConsultationRecordUpdate,
    ConsultationRecordResponse,
    ClinicalDocumentCreate,
    ClinicalDocumentResponse,
    PatientTimelineResponse,
)
from app.services.clinical_service import clinical_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, Doctor, Patient


router = APIRouter(prefix="/clinical", tags=["Clinical Records & Timeline"])


@router.post("/vitals", response_model=ApiResponse[VitalSignResponse], status_code=status.HTTP_201_CREATED)
def record_patient_vitals(
    data: VitalSignCreate,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """Records patient vitals. Validates tenant scope."""
    clinic_id = current_user.clinic_id or "default"
    try:
        vital = clinical_service.record_vitals(
            db=db,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Vitals recorded successfully", data=vital)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/patients/{patient_id}/vitals", response_model=ApiResponse[List[VitalSignResponse]])
def get_patient_vitals(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches patient vitals. Strictly validates patient identity if PATIENT role."""
    if current_user.role == "PATIENT":
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's vitals")

    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    vitals = clinical_service.get_patient_vitals(db=db, patient_id=patient_id, clinic_id=clinic_filter)
    return ApiResponse(success=True, data=vitals)


@router.post("/consultations", response_model=ApiResponse[ConsultationRecordResponse], status_code=status.HTTP_201_CREATED)
def create_consultation(
    data: ConsultationRecordCreate,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """Doctor creates a structured consultation record draft."""
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor profile not found for active user")

    clinic_id = current_user.clinic_id or "default"
    try:
        consultation = clinical_service.create_consultation(
            db=db,
            clinic_id=clinic_id,
            doctor_id=doctor.id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Consultation draft created", data=consultation)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/consultations/{id}", response_model=ApiResponse[ConsultationRecordResponse])
def update_consultation(
    id: str,
    data: ConsultationRecordUpdate,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """Doctor edits a consultation draft. Finalized records cannot be modified silently."""
    clinic_id = current_user.clinic_id or "default"
    try:
        updated = clinical_service.update_consultation(
            db=db,
            consultation_id=id,
            clinic_id=clinic_id,
            data=data,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Consultation draft updated", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/consultations/{id}/finalize", response_model=ApiResponse[ConsultationRecordResponse])
def finalize_consultation(
    id: str,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """Doctor finalizes clinical consultation. Preserves version history and completes encounter."""
    clinic_id = current_user.clinic_id or "default"
    try:
        finalized = clinical_service.finalize_consultation(
            db=db,
            consultation_id=id,
            clinic_id=clinic_id,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Consultation finalized successfully", data=finalized)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/consultations/{id}", response_model=ApiResponse[ConsultationRecordResponse])
def get_consultation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches consultation. Patients can only view finalized records of their own."""
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    rec = clinical_service.get_consultation(db, consultation_id=id, clinic_id=clinic_filter)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation record not found")

    if current_user.role == "PATIENT":
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != rec.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if not rec.is_finalized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Consultation draft not yet finalized by doctor")

    return ApiResponse(success=True, data=rec)


@router.get("/patients/{patient_id}/consultations", response_model=ApiResponse[List[ConsultationRecordResponse]])
def list_patient_consultations(
    patient_id: str,
    finalized_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists consultations for a patient. Patient role can only view their own finalized consultations."""
    is_patient = current_user.role == "PATIENT"
    if is_patient:
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's consultations")
        finalized_only = True

    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    records = clinical_service.list_patient_consultations(
        db=db,
        patient_id=patient_id,
        clinic_id=clinic_filter,
        finalized_only=finalized_only
    )
    return ApiResponse(success=True, data=records)


@router.post("/documents", response_model=ApiResponse[ClinicalDocumentResponse], status_code=status.HTTP_201_CREATED)
def upload_clinical_document(
    data: ClinicalDocumentCreate,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Uploads clinical document metadata. Validates tenant scope."""
    clinic_id = current_user.clinic_id or "default"
    doc = clinical_service.create_document(
        db=db,
        clinic_id=clinic_id,
        data=data,
        actor_id=current_user.id
    )
    return ApiResponse(success=True, message="Document recorded successfully", data=doc)


@router.get("/patients/{patient_id}/timeline", response_model=ApiResponse[PatientTimelineResponse])
def get_patient_timeline(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Longitudinal patient timeline aggregating consultations, vitals, appointments, and documents.
    Strictly verifies authorization: Patients can only access their own timeline.
    """
    is_patient = current_user.role == "PATIENT"
    if is_patient:
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not pat or pat.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot access another patient's timeline")

    clinic_id = current_user.clinic_id or "default"
    try:
        timeline = clinical_service.get_patient_timeline(
            db=db,
            patient_id=patient_id,
            clinic_id=clinic_id,
            is_patient_user=is_patient
        )
        return ApiResponse(success=True, data=timeline)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
