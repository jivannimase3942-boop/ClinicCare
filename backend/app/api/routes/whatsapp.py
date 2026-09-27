from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.integrations.whatsapp.service import whatsapp_service

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook"])


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
def get_whatsapp_status():
    configured = whatsapp_service.is_configured()
    return ApiResponse(
        success=True,
        data={
            "configured": configured,
            "message": "WhatsApp Cloud API is configured and ready" if configured else "WhatsApp Cloud API is not configured (Running in simulation mode)"
        }
    )


@router.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    valid, challenge = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if valid and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    result = await whatsapp_service.process_incoming_message(db, payload)
    return {"status": "EVENT_RECEIVED", "detail": result}
