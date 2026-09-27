from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.escalation import EscalationCreate, EscalationResponse
from app.services.escalation_service import escalation_service
from app.api.dependencies import get_current_patient, get_optional_patient
from app.models.user import Patient, User

router = APIRouter(prefix="/escalations", tags=["Escalations"])


@router.post("", response_model=ApiResponse[EscalationResponse], status_code=status.HTTP_201_CREATED)
def create_escalation(
    data: EscalationCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_patient:
            target_patient_id = current_patient.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.patient_phone:
            user = db.query(User).filter(User.phone == data.patient_phone).first()
            if user and user.patient_profile:
                target_patient_id = user.patient_profile.id
            elif user:
                pat = Patient(user_id=user.id)
                db.add(pat)
                db.commit()
                db.refresh(pat)
                target_patient_id = pat.id
        
        if not target_patient_id:
            first_patient = db.query(Patient).first()
            if first_patient:
                target_patient_id = first_patient.id
            else:
                # Create a system/guest patient profile if needed
                sys_user = db.query(User).filter(User.role == "PATIENT").first()
                if sys_user and sys_user.patient_profile:
                    target_patient_id = sys_user.patient_profile.id

        if not target_patient_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient found for escalation")

        esc = escalation_service.create_escalation(
            db=db,
            patient_id=target_patient_id,
            reason=data.reason,
            priority=data.priority or "medium",
            conversation_id=data.conversation_id,
            notes=data.notes or data.message,
        )
        return ApiResponse(success=True, message="Escalation submitted successfully", data=esc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=ApiResponse[List[EscalationResponse]])
@router.get("/my", response_model=ApiResponse[List[EscalationResponse]])
def get_my_escalations(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    if current_patient:
        escs = escalation_service.get_patient_escalations(db, current_patient.id)
    elif patient_id:
        escs = escalation_service.get_patient_escalations(db, patient_id)
    else:
        escs = escalation_service.get_all_escalations(db, status=status, priority=priority)
    return ApiResponse(success=True, data=escs)
