from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIConversationResponse,
    AIConsultationDraftRequest,
    AIReportSummaryRequest,
)
from app.ai.service import ai_service
from app.api.dependencies import get_optional_user, get_current_patient, get_current_user, require_roles
from app.models.user import User, Patient, Doctor

router = APIRouter(prefix="/ai", tags=["AI Patient Assistant"])


@router.post("/chat", response_model=ApiResponse[AIChatResponse])
def chat(
    request: AIChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    try:
        patient_id = None
        if current_user and current_user.role == "PATIENT" and current_user.patient_profile:
            patient_id = current_user.patient_profile.id

        resp = ai_service.process_chat(db=db, request=request, patient_id=patient_id, channel="web")
        return ApiResponse(success=True, data=resp)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI Chat error: {str(e)}")


@router.get("/conversations", response_model=ApiResponse[List[AIConversationResponse]])
def get_conversations(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    convs = ai_service.get_patient_conversations(db, current_patient.id)
    return ApiResponse(success=True, data=convs)


@router.get("/conversations/{id}", response_model=ApiResponse[AIConversationResponse])
def get_conversation(
    id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    conv = ai_service.get_conversation_by_id(db, conversation_id=id, patient_id=current_patient.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized")
    return ApiResponse(success=True, data=conv)


@router.post("/clinical/draft-note", response_model=ApiResponse[Dict[str, Any]])
def draft_clinical_note(
    request: AIConsultationDraftRequest,
    current_user: User = Depends(require_roles(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    """
    Physician requests AI consultation note draft.
    Human verification is mandatory. AI does not autonomously diagnose or prescribe.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor profile not found for active user")

    from app.services.clinical_ai_service import clinical_ai_service
    clinic_id = current_user.clinic_id or "default"
    try:
        draft = clinical_ai_service.draft_consultation_note(
            db=db,
            patient_id=request.patient_id,
            doctor_id=doctor.id,
            clinic_id=clinic_id,
            raw_notes=request.raw_notes,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Clinical draft generated for physician review", data=draft)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/clinical/summarize-report", response_model=ApiResponse[Dict[str, Any]])
def summarize_lab_report(
    request: AIReportSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates non-diagnostic AI summary of a released laboratory diagnostic report.
    """
    from app.services.clinical_ai_service import clinical_ai_service
    clinic_id = current_user.clinic_id or "default"
    try:
        summary = clinical_ai_service.summarize_lab_report(
            db=db,
            order_id=request.order_id,
            clinic_id=clinic_id,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, data=summary)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
