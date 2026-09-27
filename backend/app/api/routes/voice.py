from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.voice import VoiceCallCreate, VoiceCallResponse
from app.services.voice_service import voice_service
from app.api.dependencies import get_current_patient, get_optional_patient
from app.models.user import Patient, User

router = APIRouter(prefix="/voice", tags=["AI Voice Calls"])


@router.post("/request", response_model=ApiResponse[VoiceCallResponse], status_code=status.HTTP_201_CREATED)
def request_voice_call(
    data: VoiceCallCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_patient:
            target_patient_id = current_patient.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.phone:
            user = db.query(User).filter(User.phone == data.phone).first()
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
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient found for voice call request")

        call = voice_service.request_voice_call(db, patient_id=target_patient_id, data=data)
        return ApiResponse(success=True, message="Voice call requested successfully", data=call)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=ApiResponse[List[VoiceCallResponse]])
@router.get("/my", response_model=ApiResponse[List[VoiceCallResponse]])
def get_my_voice_calls(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    if current_patient:
        calls = voice_service.get_patient_voice_calls(db, current_patient.id)
    elif patient_id:
        calls = voice_service.get_patient_voice_calls(db, patient_id)
    else:
        calls = voice_service.get_all_voice_calls(db, status=status)
    return ApiResponse(success=True, data=calls)
