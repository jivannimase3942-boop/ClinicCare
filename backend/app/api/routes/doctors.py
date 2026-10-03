from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.doctor import DoctorResponse, DoctorSlotResponse
from app.schemas.appointment import DoctorScheduleUpdate, DoctorLeaveCreate, DoctorLeaveResponse
from app.services.doctor_service import doctor_service
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User

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


@router.patch("/{id}/schedule", response_model=ApiResponse[DoctorResponse])
def update_doctor_schedule(
    id: str,
    data: DoctorScheduleUpdate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    # If doctor, ensure modifying own schedule
    if current_user.role == "DOCTOR":
        if not current_user.doctor_profile or current_user.doctor_profile.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another doctor's schedule")

    try:
        updated = doctor_service.update_doctor_schedule(db, doctor_id=id, update_data=data.model_dump(exclude_unset=True))
        return ApiResponse(success=True, message="Doctor schedule updated", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/leaves", response_model=ApiResponse[DoctorLeaveResponse], status_code=status.HTTP_201_CREATED)
def add_doctor_leave(
    id: str,
    data: DoctorLeaveCreate,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    if current_user.role == "DOCTOR":
        if not current_user.doctor_profile or current_user.doctor_profile.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot apply leave for another doctor")

    try:
        leave = doctor_service.add_doctor_leave(
            db=db,
            doctor_id=id,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
            clinic_id=current_user.clinic_id,
        )
        resp = DoctorLeaveResponse(
            id=leave.id,
            clinic_id=leave.clinic_id,
            doctor_id=leave.doctor_id,
            doctor_name=leave.doctor.user.full_name if leave.doctor and leave.doctor.user else "Doctor",
            start_date=leave.start_date,
            end_date=leave.end_date,
            reason=leave.reason,
            is_approved=leave.is_approved,
            created_at=leave.created_at,
        )
        return ApiResponse(success=True, message="Doctor leave recorded", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}/leaves", response_model=ApiResponse[List[DoctorLeaveResponse]])
def get_doctor_leaves(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    leaves = doctor_service.get_doctor_leaves(db, doctor_id=id, clinic_id=clinic_filter)
    result = [
        DoctorLeaveResponse(
            id=l.id,
            clinic_id=l.clinic_id,
            doctor_id=l.doctor_id,
            doctor_name=l.doctor.user.full_name if l.doctor and l.doctor.user else "Doctor",
            start_date=l.start_date,
            end_date=l.end_date,
            reason=l.reason,
            is_approved=l.is_approved,
            created_at=l.created_at,
        )
        for l in leaves
    ]
    return ApiResponse(success=True, data=result)

