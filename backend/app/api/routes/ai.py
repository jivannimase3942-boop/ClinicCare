from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.ai import AIChatRequest, AIChatResponse, AIConversationResponse
from app.ai.service import ai_service
from app.api.dependencies import get_optional_user, get_current_patient
from app.models.user import User, Patient

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
