import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.ai import AIConversation, AIMessage
from app.schemas.ai import AIChatRequest, AIChatResponse, AIConversationResponse, AIMessageResponse
from app.ai.safety import MedicalSafetyGuard
from app.ai.provider import get_ai_provider
from app.ai.tools import escalate_to_front_desk


class AIService:
    @staticmethod
    def get_or_create_conversation(db: Session, conversation_id: Optional[str], patient_id: Optional[str], channel: str = "web") -> AIConversation:
        if conversation_id:
            conv = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
            if conv:
                if patient_id and not conv.patient_id:
                    conv.patient_id = patient_id
                    db.commit()
                return conv

        conv = AIConversation(
            patient_id=patient_id,
            channel=channel,
            title="Patient Assistant Chat",
            is_active=True
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def process_chat(
        db: Session,
        request: AIChatRequest,
        patient_id: Optional[str] = None,
        channel: str = "web"
    ) -> AIChatResponse:
        conv = AIService.get_or_create_conversation(db, request.conversation_id, patient_id, channel)

        # 1. Log patient message
        user_msg = AIMessage(
            conversation_id=conv.id,
            sender="patient",
            content=request.message,
        )
        db.add(user_msg)
        db.commit()

        # 2. Check Emergency Guardrail
        is_emerg, emerg_notice = MedicalSafetyGuard.check_emergency(request.message)
        if is_emerg:
            if patient_id:
                escalate_to_front_desk(
                    db=db,
                    patient_id=patient_id,
                    reason="emergency",
                    priority="emergency",
                    notes=f"Emergency detected: {request.message}",
                    conversation_id=conv.id,
                )
            ai_msg = AIMessage(
                conversation_id=conv.id,
                sender="ai",
                content=emerg_notice,
                intent="emergency_escalation",
            )
            db.add(ai_msg)
            db.commit()
            return AIChatResponse(
                conversation_id=conv.id,
                reply=emerg_notice,
                response=emerg_notice,
                intent="emergency_escalation",
                is_emergency=True,
                escalation_triggered=True,
                suggested_actions=["Call Emergency 911", "Book Doctor Appointment"]
            )

        # 3. Check Clinical Safety Guardrail
        is_diag, diag_notice = MedicalSafetyGuard.check_clinical_advice(request.message)
        if is_diag:
            ai_msg = AIMessage(
                conversation_id=conv.id,
                sender="ai",
                content=diag_notice,
                intent="clinical_advice_guardrail",
            )
            db.add(ai_msg)
            db.commit()
            return AIChatResponse(
                conversation_id=conv.id,
                reply=diag_notice,
                response=diag_notice,
                intent="clinical_advice_guardrail",
                is_emergency=False,
                escalation_triggered=False,
                suggested_actions=["Book Appointment", "Find Specialists"]
            )

        # 4. Load Conversation History
        history_msgs = db.query(AIMessage).filter(
            AIMessage.conversation_id == conv.id
        ).order_by(AIMessage.created_at.desc()).limit(10).all()
        history_msgs.reverse()

        formatted_history = [{"sender": m.sender, "content": m.content} for m in history_msgs]

        # 5. Generate AI / Intent Response
        provider = get_ai_provider()
        res = provider.generate_chat_response(
            db=db,
            patient_id=patient_id,
            user_message=request.message,
            conversation_history=formatted_history,
            conversation_id=conv.id
        )

        reply = res.get("reply", "How can I assist your health needs today?")
        intent = res.get("intent", "general")
        tool_calls = res.get("tool_calls", [])
        suggested_actions = res.get("suggested_actions", ["Book Appointment", "Check Doctors", "Report Status"])

        # 6. Save AI reply to database
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        ai_msg = AIMessage(
            conversation_id=conv.id,
            sender="ai",
            content=reply,
            intent=intent,
            tool_calls=tool_calls_json,
        )
        db.add(ai_msg)
        db.commit()

        has_escalation = any(
            (t.get("tool_name") if isinstance(t, dict) else getattr(t, "tool_name", "")) == "escalate_to_front_desk"
            for t in (tool_calls or [])
        )

        return AIChatResponse(
            conversation_id=conv.id,
            reply=reply,
            response=reply,
            intent=intent,
            tool_calls=tool_calls,
            is_emergency=False,
            escalation_triggered=has_escalation,
            suggested_actions=suggested_actions
        )

    @staticmethod
    def get_patient_conversations(db: Session, patient_id: str) -> List[AIConversationResponse]:
        convs = db.query(AIConversation).filter(
            AIConversation.patient_id == patient_id
        ).order_by(AIConversation.updated_at.desc()).all()
        
        result = []
        for c in convs:
            msgs = [AIMessageResponse.model_validate(m) for m in c.messages]
            result.append(
                AIConversationResponse(
                    id=c.id,
                    patient_id=c.patient_id,
                    channel=c.channel,
                    title=c.title,
                    is_active=c.is_active,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    messages=msgs
                )
            )
        return result

    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: str, patient_id: Optional[str] = None) -> Optional[AIConversationResponse]:
        query = db.query(AIConversation).filter(AIConversation.id == conversation_id)
        if patient_id:
            query = query.filter(AIConversation.patient_id == patient_id)
        c = query.first()
        if not c:
            return None
        msgs = [AIMessageResponse.model_validate(m) for m in c.messages]
        return AIConversationResponse(
            id=c.id,
            patient_id=c.patient_id,
            channel=c.channel,
            title=c.title,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=msgs
        )

    @staticmethod
    def get_all_conversations(db: Session, limit: int = 50) -> List[AIConversationResponse]:
        convs = db.query(AIConversation).order_by(AIConversation.created_at.desc()).limit(limit).all()
        result = []
        for c in convs:
            msgs = [AIMessageResponse.model_validate(m) for m in c.messages]
            result.append(
                AIConversationResponse(
                    id=c.id,
                    patient_id=c.patient_id,
                    channel=c.channel,
                    title=c.title,
                    is_active=c.is_active,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    messages=msgs
                )
            )
        return result


ai_service = AIService()

