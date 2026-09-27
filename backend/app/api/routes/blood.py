from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.blood import (
    BloodBankResponse,
    BloodGroupSearchResult,
    BloodInventoryItem,
    BloodInventoryUpdate,
    BloodRequestCreate,
    BloodRequestResponse,
    BloodRequestStatusUpdate,
    BloodRequestMatchPayload,
)
from app.services.blood_service import blood_service
from app.api.dependencies import require_roles, get_optional_patient
from app.models.user import Patient

router = APIRouter(prefix="/blood", tags=["Blood Banks & Availability"])


@router.get("/banks", response_model=ApiResponse[List[BloodBankResponse]])
def list_blood_banks(
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    banks = blood_service.get_all_blood_banks(db, city=city)
    return ApiResponse(success=True, data=banks)


@router.get("/search", response_model=ApiResponse[List[BloodGroupSearchResult]])
def search_blood(
    blood_group: Optional[str] = Query(None, description="Blood group e.g. A+, O+, B-, AB+"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db)
):
    results = blood_service.search_blood_group(db, blood_group=blood_group or "", city=city)
    return ApiResponse(success=True, data=results)


@router.patch("/inventory/{id}", response_model=ApiResponse[BloodInventoryItem], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def update_inventory_units(id: str, data: BloodInventoryUpdate, db: Session = Depends(get_db)):
    try:
        item = blood_service.update_inventory_units(db, id, data)
        return ApiResponse(success=True, message="Blood inventory updated", data=item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/requests", response_model=ApiResponse[BloodRequestResponse], status_code=status.HTTP_201_CREATED)
def create_blood_request(
    data: BloodRequestCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        patient_id = current_patient.id if current_patient else data.patient_id
        req = blood_service.create_blood_request(db, data, patient_id=patient_id)
        return ApiResponse(success=True, message="Blood requirement request submitted successfully", data=req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/requests", response_model=ApiResponse[List[BloodRequestResponse]])
def list_blood_requests(
    status: Optional[str] = Query(None),
    blood_group: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    target_patient_id = current_patient.id if current_patient else patient_id
    requests = blood_service.get_blood_requests(
        db, status=status, blood_group=blood_group, urgency=urgency, patient_id=target_patient_id
    )
    return ApiResponse(success=True, data=requests)


@router.patch("/requests/{id}", response_model=ApiResponse[BloodRequestResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def update_blood_request(id: str, data: BloodRequestStatusUpdate, db: Session = Depends(get_db)):
    try:
        req = blood_service.update_blood_request_status(db, id, data)
        return ApiResponse(success=True, message="Blood request updated successfully", data=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/requests/{id}/match", response_model=ApiResponse[BloodRequestResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def match_blood_bank_to_request(id: str, data: BloodRequestMatchPayload, db: Session = Depends(get_db)):
    try:
        req = blood_service.match_blood_bank(db, id, data.blood_bank_id, data.notes)
        return ApiResponse(success=True, message="Blood bank matched and recorded", data=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

