import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.voice import VoiceCallRequest
from app.schemas.voice import VoiceCallCreate, VoiceCallResponse, VoiceCallUpdateStatus


class VoiceCallService:
    @staticmethod
    def _format_voice(v: VoiceCallRequest) -> VoiceCallResponse:
        patient_name = v.patient.user.full_name if v.patient and v.patient.user else None
        return VoiceCallResponse(
            id=v.id,
            patient_id=v.patient_id,
            patient_name=patient_name,
            phone=v.phone,
            reason=v.reason,
            status=v.status,
            requested_at=v.requested_at,
            completed_at=v.completed_at,
            notes=v.notes,
            created_at=v.created_at,
        )

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.VOICE_API_KEY and settings.VOICE_API_URL)

    @staticmethod
    def request_voice_call(db: Session, patient_id: str, data: VoiceCallCreate) -> VoiceCallResponse:
        phone_num = data.phone
        if not phone_num:
            from app.models.user import Patient
            pat = db.query(Patient).filter(Patient.id == patient_id).first()
            if pat and pat.user and pat.user.phone:
                phone_num = pat.user.phone
            else:
                phone_num = "N/A"

        # Check external voice API configuration
        external_note = None
        if not VoiceCallService.is_configured():
            external_note = "Voice call service unconfigured (VOICE_API_KEY/VOICE_API_URL missing). Registered in internal queue."
        else:
            try:
                # Dispatch to external Voice Calling Server
                headers = {"Authorization": f"Bearer {settings.VOICE_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "to": phone_num,
                    "agent_id": settings.VOICE_AGENT_ID or "default-hospital-agent",
                    "reason": data.reason,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(settings.VOICE_API_URL, json=payload, headers=headers)
                    if resp.status_code in [200, 201, 202]:
                        external_note = f"Dispatched to external voice server: {resp.status_code}"
                    else:
                        external_note = f"External voice server returned error status: {resp.status_code}"
            except Exception as ex:
                external_note = f"External voice server connection error: {str(ex)}"

        voice = VoiceCallRequest(
            patient_id=patient_id,
            phone=phone_num,
            reason=data.reason,
            status="requested",
            notes=external_note,
            requested_at=datetime.now(timezone.utc),
        )
        db.add(voice)
        db.commit()
        db.refresh(voice)
        return VoiceCallService._format_voice(voice)

    @staticmethod
    def get_patient_voice_calls(db: Session, patient_id: str) -> List[VoiceCallResponse]:
        calls = db.query(VoiceCallRequest).filter(
            VoiceCallRequest.patient_id == patient_id
        ).order_by(VoiceCallRequest.created_at.desc()).all()
        return [VoiceCallService._format_voice(c) for c in calls]

    @staticmethod
    def get_all_voice_calls(db: Session, status: Optional[str] = None) -> List[VoiceCallResponse]:
        query = db.query(VoiceCallRequest)
        if status:
            query = query.filter(VoiceCallRequest.status == status)
        calls = query.order_by(VoiceCallRequest.created_at.desc()).all()
        return [VoiceCallService._format_voice(c) for c in calls]

    @staticmethod
    def update_voice_status(db: Session, voice_id: str, data: VoiceCallUpdateStatus) -> VoiceCallResponse:
        voice = db.query(VoiceCallRequest).filter(VoiceCallRequest.id == voice_id).first()
        if not voice:
            raise ValueError("Voice call request not found")
        voice.status = data.status
        if data.notes:
            voice.notes = data.notes
        if data.status in ["completed", "failed", "cancelled"]:
            voice.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(voice)
        return VoiceCallService._format_voice(voice)


voice_service = VoiceCallService()

