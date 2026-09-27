import re
import httpx
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.appointment import Appointment
from app.models.feedback import Feedback
from app.schemas.ai import AIChatRequest
from app.schemas.feedback import FeedbackCreate
from app.services.feedback_service import feedback_service
from app.ai.service import ai_service


class WhatsAppService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.WA_PHONE_NUMBER_ID and settings.WA_ACCESS_TOKEN)

    @staticmethod
    def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Tuple[bool, Optional[str]]:
        if mode == "subscribe" and token == settings.WA_VERIFY_TOKEN:
            return True, challenge
        return False, None

    @staticmethod
    async def send_text_message(to_phone: str, message_body: str) -> Dict[str, Any]:
        if not WhatsAppService.is_configured():
            return {
                "status": "unconfigured",
                "message": "WhatsApp Cloud API credentials not configured. Running in controlled dev mode.",
                "recipient": to_phone,
                "text": message_body,
            }

        url = f"https://graph.facebook.com/{settings.WA_API_VERSION}/{settings.WA_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_body},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _parse_feedback_rating(text: str) -> Tuple[Optional[int], Optional[str]]:
        trimmed = text.strip()
        if trimmed in ["1", "2", "3", "4", "5"]:
            return int(trimmed), None
        match = re.match(r"^(?:rating\s*[:=]?\s*)?([1-5])(?:\s*(?:/5|\*|stars?))?\s*[-:,.]?\s*(.*)$", trimmed, re.IGNORECASE)
        if match:
            rating = int(match.group(1))
            comment = match.group(2).strip() or None
            return rating, comment
        return None, None

    @staticmethod
    async def process_incoming_message(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return {"status": "ignored", "reason": "No messages found in payload"}

            msg_obj = messages[0]
            from_phone = msg_obj.get("from")
            text_body = msg_obj.get("text", {}).get("body", "")

            if not text_body or not from_phone:
                return {"status": "ignored", "reason": "Empty text or phone"}

            # Lookup patient by phone number
            patient_id = None
            patient_name = "Patient"
            user = db.query(User).filter(User.phone == from_phone).first()
            if user:
                patient_name = user.full_name
                if user.patient_profile:
                    patient_id = user.patient_profile.id

            # 1. Check Pending Feedback Rating Handling
            rating_val, rating_comment = WhatsAppService._parse_feedback_rating(text_body)
            if rating_val is not None and patient_id:
                completed_app = db.query(Appointment).filter(
                    Appointment.patient_id == patient_id,
                    Appointment.status == "completed"
                ).outerjoin(Feedback, Appointment.id == Feedback.appointment_id).filter(
                    Feedback.id == None
                ).order_by(Appointment.appointment_date.desc()).first()

                if completed_app:
                    feedback_service.submit_feedback(
                        db=db,
                        patient_id=patient_id,
                        data=FeedbackCreate(
                            appointment_id=completed_app.id,
                            rating=rating_val,
                            comment=rating_comment or f"WhatsApp rating response ({rating_val}/5)"
                        )
                    )
                    reply_text = f"Thank you, {patient_name}! Your rating of {rating_val}/5 has been saved. We appreciate your valuable feedback."
                    send_res = await WhatsAppService.send_text_message(from_phone, reply_text)
                    return {
                        "status": "feedback_recorded",
                        "from": from_phone,
                        "rating": rating_val,
                        "comment": rating_comment,
                        "reply": reply_text,
                        "send_result": send_res
                    }

            # 2. Route to Patient WhatsApp AI Agent
            ai_req = AIChatRequest(message=text_body)
            chat_resp = ai_service.process_chat(db, ai_req, patient_id=patient_id, channel="whatsapp")

            # 3. Send response back to user
            send_result = await WhatsAppService.send_text_message(from_phone, chat_resp.reply)

            return {
                "status": "processed",
                "from": from_phone,
                "user_message": text_body,
                "ai_reply": chat_resp.reply,
                "intent": chat_resp.intent,
                "is_emergency": chat_resp.is_emergency,
                "send_result": send_result,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


whatsapp_service = WhatsAppService()

