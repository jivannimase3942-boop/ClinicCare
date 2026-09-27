from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.reminder import FollowUpReminderResponse, FollowUpReminderCreate
from app.services.reminder_service import reminder_service
from app.api.dependencies import require_roles, get_optional_patient
from app.models.user import Patient

router = APIRouter(prefix="/reminders", tags=["Follow-Up Reminders"])


@router.get("", response_model=ApiResponse[List[FollowUpReminderResponse]])
def list_reminders(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    target_patient_id = current_patient.id if current_patient else patient_id
    reminders = reminder_service.get_reminders(db, patient_id=target_patient_id, status=status)
    return ApiResponse(success=True, data=reminders)


@router.post("", response_model=ApiResponse[FollowUpReminderResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR"]))])
def create_reminder(data: FollowUpReminderCreate, db: Session = Depends(get_db)):
    try:
        rem = reminder_service.create_reminder(db, data)
        return ApiResponse(success=True, message="Reminder scheduled successfully", data=rem)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/dispatch", response_model=ApiResponse[FollowUpReminderResponse])
def trigger_dispatch(id: str, db: Session = Depends(get_db)):
    try:
        rem = reminder_service.trigger_simulated_dispatch(db, id)
        return ApiResponse(success=True, message="Simulated reminder dispatched to patient", data=rem)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
