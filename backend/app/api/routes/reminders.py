from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.reminder import FollowUpReminderResponse, FollowUpReminderCreate
from app.services.reminder_service import reminder_service
from app.api.dependencies import require_roles, get_optional_user
from app.models.user import User, Patient

router = APIRouter(prefix="/reminders", tags=["Follow-Up Reminders"])


@router.get("", response_model=ApiResponse[List[FollowUpReminderResponse]])
def list_reminders(
    patient_id: Optional[str] = Query(None),
    status_param: Optional[str] = Query(None, alias="status"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view reminders",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user.role == "PATIENT":
        target_patient_id = current_user.patient_profile.id if current_user.patient_profile else "__none__"
        reminders = reminder_service.get_reminders(db, patient_id=target_patient_id, status=status_param)
        return ApiResponse(success=True, data=reminders)

    if current_user.role in ["ADMIN", "FRONT_DESK", "DOCTOR", "SUPER_ADMIN"]:
        reminders = reminder_service.get_reminders(db, patient_id=patient_id, status=status_param)
        return ApiResponse(success=True, data=reminders)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post("", response_model=ApiResponse[FollowUpReminderResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR"]))])
def create_reminder(data: FollowUpReminderCreate, db: Session = Depends(get_db)):
    try:
        rem = reminder_service.create_reminder(db, data)
        return ApiResponse(success=True, message="Reminder scheduled successfully", data=rem)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/dispatch", response_model=ApiResponse[FollowUpReminderResponse], dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR"]))])
def trigger_dispatch(id: str, db: Session = Depends(get_db)):
    try:
        rem = reminder_service.trigger_simulated_dispatch(db, id)
        return ApiResponse(success=True, message="Simulated reminder dispatched to patient", data=rem)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
