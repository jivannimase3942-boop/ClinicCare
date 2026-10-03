from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.schemas.common import ApiResponse
from app.api.dependencies import require_roles
from app.models.user import User
from app.services.automation_service import automation_service, SUPPORTED_AUTOMATION_EVENTS


router = APIRouter(prefix="/automation", tags=["Healthcare Automation Engine"])


class AutomationEventTriggerRequest(BaseModel):
    event_name: str
    recipient_user_id: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.get("/events", response_model=ApiResponse[Dict[str, Any]])
def get_automation_capabilities(
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"]))
):
    """
    Returns supported healthcare automation events and honest provider readiness states.
    """
    return ApiResponse(
        success=True,
        data={
            "supported_events": sorted(list(SUPPORTED_AUTOMATION_EVENTS)),
            "providers_configured": {
                "in_app": True,
                "n8n_webhook": bool(getattr(settings, "N8N_WEBHOOK_URL", None)),
                "whatsapp": bool(settings.WA_PHONE_NUMBER_ID and settings.WA_ACCESS_TOKEN),
                "email_smtp": bool(getattr(settings, "SMTP_HOST", None) and getattr(settings, "SMTP_USER", None)),
                "sms_gateway": bool(getattr(settings, "SMS_API_KEY", None)),
            }
        }
    )


@router.post("/events/trigger", response_model=ApiResponse[Dict[str, Any]])
def trigger_automation_event(
    request: AutomationEventTriggerRequest,
    current_user: User = Depends(require_roles(["ADMIN", "DOCTOR", "FRONT_DESK"])),
    db: Session = Depends(get_db)
):
    """
    Triggers a standardized healthcare event across available channels.
    Provides honest status reporting: unconfigured providers are explicitly reported.
    """
    clinic_id = current_user.clinic_id or "default"
    try:
        result = automation_service.trigger_event(
            db=db,
            event_name=request.event_name,
            clinic_id=clinic_id,
            recipient_user_id=request.recipient_user_id,
            title=request.title,
            message=request.message,
            payload=request.payload,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message=f"Event {request.event_name} dispatched", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
