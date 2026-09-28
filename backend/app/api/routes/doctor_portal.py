from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.appointment import AppointmentResponse, AppointmentStatusUpdate
from app.api.dependencies import require_roles, get_current_user
from app.models.user import User, Doctor, Patient
from app.services.appointment_service import appointment_service

router = APIRouter(prefix="/doctor", tags=["Doctor Portal"], dependencies=[Depends(require_roles(["DOCTOR", "ADMIN"]))])


@router.get("/appointments", response_model=ApiResponse[List[AppointmentResponse]])
def get_my_doctor_appointments(
    date_filter: Optional[date] = Query(None, alias="date"),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.doctor_profile and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No doctor profile associated with user")
    
    doc_id = current_user.doctor_profile.id if current_user.doctor_profile else None
    apps = appointment_service.get_all_appointments(
        db, doctor_id=doc_id, status=status_filter, date_filter=date_filter
    )
    return ApiResponse(success=True, data=apps)


@router.patch("/appointments/{id}/status", response_model=ApiResponse[AppointmentResponse])
def update_doctor_appointment_status(
    id: str,
    data: Optional[AppointmentStatusUpdate] = Body(None),
    status_param: Optional[str] = Query(None, alias="status", description="completed, cancelled, no_show, confirmed"),
    notes: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_status = (data.status if data and data.status else status_param)
    target_notes = (data.notes if data and data.notes is not None else notes)
    if not target_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")

    existing_app = appointment_service.get_appointment_by_id(db, id)
    if not existing_app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if current_user.role == "DOCTOR":
        if not current_user.doctor_profile or existing_app.doctor_id != current_user.doctor_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot modify another doctor's appointment")

    try:
        app = appointment_service.update_appointment_status(db, id, target_status, target_notes)
        return ApiResponse(success=True, message="Appointment status updated", data=app)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

