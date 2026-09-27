from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.doctor import DoctorResponse, DoctorSlotResponse
from app.services.doctor_service import doctor_service

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=ApiResponse[List[DoctorResponse]])
def list_doctors(
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    search: Optional[str] = Query(None, description="Search by doctor name or specialization"),
    db: Session = Depends(get_db)
):
    docs = doctor_service.get_doctors(db, department_id=department_id, search=search)
    return ApiResponse(success=True, data=docs)


@router.get("/{id}", response_model=ApiResponse[DoctorResponse])
def get_doctor(id: str, db: Session = Depends(get_db)):
    doc = doctor_service.get_doctor_by_id(db, id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return ApiResponse(success=True, data=doc)


@router.get("/{id}/slots", response_model=ApiResponse[List[DoctorSlotResponse]])
def get_doctor_slots(
    id: str,
    date_query: Optional[date] = Query(None, alias="date", description="Slot date e.g. 2026-09-28"),
    slot_date: Optional[date] = Query(None, alias="slot_date", description="Slot date e.g. 2026-09-28"),
    db: Session = Depends(get_db)
):
    target_date = date_query or slot_date or date.today()
    try:
        slots = doctor_service.get_or_generate_slots_for_date(db, doctor_id=id, slot_date=target_date)
        return ApiResponse(success=True, data=slots)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
