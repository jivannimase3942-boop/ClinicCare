from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.ambulance import (
    AmbulanceResponse,
    AmbulanceCreate,
    AmbulanceStatusUpdate,
    AmbulanceRequestCreate,
    AmbulanceRequestResponse,
    AmbulanceRequestStatusUpdate,
    AmbulanceAssignPayload,
)
from app.services.ambulance_service import ambulance_service
from app.api.dependencies import require_roles, get_optional_patient, get_current_user
from app.models.user import Patient, User

router = APIRouter(prefix="/ambulances", tags=["Ambulances & Fleet"])


@router.get("", response_model=ApiResponse[List[AmbulanceResponse]])
def list_ambulances(
    status: Optional[str] = Query(None, description="Filter by status: available, busy, offline"),
    db: Session = Depends(get_db)
):
    ambulances = ambulance_service.get_all_ambulances(db, status=status)
    return ApiResponse(success=True, data=ambulances)


@router.post("", response_model=ApiResponse[AmbulanceResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def create_ambulance(data: AmbulanceCreate, db: Session = Depends(get_db)):
    try:
        amb = ambulance_service.create_ambulance(db, data)
        return ApiResponse(success=True, message="Ambulance registered successfully", data=amb)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{id}", response_model=ApiResponse[AmbulanceResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def update_ambulance_status(id: str, data: AmbulanceStatusUpdate, db: Session = Depends(get_db)):
    try:
        amb = ambulance_service.update_ambulance_status(db, id, data)
        return ApiResponse(success=True, message="Ambulance status updated", data=amb)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/request", response_model=ApiResponse[AmbulanceRequestResponse], status_code=status.HTTP_201_CREATED)
def request_ambulance(
    data: AmbulanceRequestCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        patient_id = current_patient.id if current_patient else data.patient_id
        req = ambulance_service.request_ambulance(db, data, patient_id=patient_id)
        return ApiResponse(success=True, message="Ambulance request dispatched successfully", data=req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/requests", response_model=ApiResponse[List[AmbulanceRequestResponse]])
def list_ambulance_requests(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "PATIENT":
        target_patient_id = current_user.patient_profile.id if current_user.patient_profile else "__none__"
    elif current_user.role in ["ADMIN", "FRONT_DESK", "DOCTOR", "SUPER_ADMIN"]:
        target_patient_id = patient_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    requests = ambulance_service.get_ambulance_requests(db, status=status, patient_id=target_patient_id, priority=priority)
    return ApiResponse(success=True, data=requests)


@router.patch("/requests/{id}", response_model=ApiResponse[AmbulanceRequestResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def update_request_status(id: str, data: AmbulanceRequestStatusUpdate, db: Session = Depends(get_db)):
    try:
        req = ambulance_service.update_request_status(db, id, data)
        return ApiResponse(success=True, message="Ambulance request updated", data=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/requests/{id}/assign", response_model=ApiResponse[AmbulanceRequestResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def assign_ambulance(id: str, data: AmbulanceAssignPayload, db: Session = Depends(get_db)):
    try:
        req = ambulance_service.assign_ambulance_to_request(db, id, data.ambulance_id, data.notes)
        return ApiResponse(success=True, message="Ambulance assigned and dispatched", data=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
