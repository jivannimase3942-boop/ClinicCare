from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import feedback_service
from app.api.dependencies import get_current_user, get_optional_user
from app.models.user import Patient, User
from app.models.appointment import Appointment

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=ApiResponse[FeedbackResponse], status_code=status.HTTP_201_CREATED)
def submit_feedback(
    data: FeedbackCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_user and current_user.role == "PATIENT":
            if not current_user.patient_profile:
                pat = Patient(user_id=current_user.id)
                db.add(pat)
                db.commit()
                db.refresh(pat)
                target_patient_id = pat.id
            else:
                target_patient_id = current_user.patient_profile.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.appointment_id:
            app = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
            if app:
                target_patient_id = app.patient_id
        elif current_user and current_user.patient_profile:
            target_patient_id = current_user.patient_profile.id
        else:
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
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile:
            return ApiResponse(success=True, data=[])
        fbs = feedback_service.get_patient_feedbacks(db, current_user.patient_profile.id)
        return ApiResponse(success=True, data=fbs)

    if current_user and current_user.role in ["ADMIN", "FRONT_DESK"]:
        if patient_id:
            fbs = feedback_service.get_patient_feedbacks(db, patient_id)
        else:
            fbs = feedback_service.get_all_feedbacks(db)
        return ApiResponse(success=True, data=fbs)

    if patient_id:
        fbs = feedback_service.get_patient_feedbacks(db, patient_id)
        return ApiResponse(success=True, data=fbs)

    return ApiResponse(success=True, data=feedback_service.get_all_feedbacks(db))
