from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import feedback_service
from app.api.dependencies import get_current_patient, get_optional_patient
from app.models.user import Patient, User
from app.models.appointment import Appointment

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=ApiResponse[FeedbackResponse], status_code=status.HTTP_201_CREATED)
def submit_feedback(
    data: FeedbackCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_patient:
            target_patient_id = current_patient.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.appointment_id:
            app = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
            if app:
                target_patient_id = app.patient_id
        elif data.phone:
            user = db.query(User).filter(User.phone == data.phone).first()
            if user and user.patient_profile:
                target_patient_id = user.patient_profile.id

        if not target_patient_id:
            first_patient = db.query(Patient).first()
            if first_patient:
                target_patient_id = first_patient.id
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient profile found for feedback")

        fb = feedback_service.submit_feedback(db, target_patient_id, data)
        return ApiResponse(success=True, message="Feedback submitted successfully", data=fb)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=ApiResponse[List[FeedbackResponse]])
@router.get("/my", response_model=ApiResponse[List[FeedbackResponse]])
def get_my_feedback(
    patient_id: Optional[str] = Query(None),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    if current_patient:
        fbs = feedback_service.get_patient_feedbacks(db, current_patient.id)
    elif patient_id:
        fbs = feedback_service.get_patient_feedbacks(db, patient_id)
    else:
        fbs = feedback_service.get_all_feedbacks(db)
    return ApiResponse(success=True, data=fbs)
