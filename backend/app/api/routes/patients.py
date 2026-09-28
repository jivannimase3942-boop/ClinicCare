from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.patient import (
    PatientProfileResponse,
    PatientProfileUpdate,
    VisitHistoryResponse,
    VisitHistoryCreate,
)
from app.services.patient_service import patient_service
from app.api.dependencies import require_roles, get_optional_user, get_current_user
from app.models.user import User, Patient

router = APIRouter(prefix="/patients", tags=["Patient Records & History"])


@router.get("", response_model=ApiResponse[List[PatientProfileResponse]])
def search_patients(
    search: Optional[str] = Query(None, description="Search query by name, ID, phone, email"),
    blood_group: Optional[str] = Query(None, description="Filter by blood group"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    # Patient role is forbidden from browsing general patient registry
    if current_user and current_user.role == "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Patients cannot browse patient registry")

    patients = patient_service.search_patients(db, query_str=search, blood_group=blood_group, gender=gender)
    return ApiResponse(success=True, data=patients)


@router.get("/{id}", response_model=ApiResponse[PatientProfileResponse])
def get_patient_profile(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    # Patient privacy check: Patient can only view their own profile
    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or current_user.patient_profile.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's medical profile")

    pat = patient_service.get_patient_by_id(db, id)
    if not pat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return ApiResponse(success=True, data=pat)


@router.patch("/{id}", response_model=ApiResponse[PatientProfileResponse])
def update_patient_profile(
    id: str,
    data: PatientProfileUpdate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user and current_user.role == "PATIENT":
            if not current_user.patient_profile or current_user.patient_profile.id != id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot edit another patient's profile")
        elif current_user and current_user.role not in ["ADMIN", "FRONT_DESK", "DOCTOR"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        updated = patient_service.update_patient_profile(db, id, data)
        return ApiResponse(success=True, message="Profile updated successfully", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{id}/visits", response_model=ApiResponse[List[VisitHistoryResponse]])
def get_patient_visits(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    # Patient privacy check: Patient can only view their own visits
    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or current_user.patient_profile.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's visit history")

    visits = patient_service.get_patient_visits(db, patient_id=id)
    return ApiResponse(success=True, data=visits)


@router.post("/{id}/visits", response_model=ApiResponse[VisitHistoryResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR"]))])
def record_patient_visit(id: str, data: VisitHistoryCreate, db: Session = Depends(get_db)):
    try:
        data.patient_id = id
        visit = patient_service.record_visit(db, data)
        return ApiResponse(success=True, message="Visit history recorded successfully", data=visit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
