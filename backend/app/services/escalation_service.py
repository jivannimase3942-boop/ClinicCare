from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.escalation import Escalation
from app.models.user import User
from app.schemas.escalation import EscalationCreate, EscalationResponse, EscalationUpdate


class EscalationService:
    @staticmethod
    def _format_escalation(e: Escalation) -> EscalationResponse:
        patient_name = e.patient.user.full_name if e.patient and e.patient.user else None
        patient_phone = e.patient.user.phone if e.patient and e.patient.user else None
        patient_email = e.patient.user.email if e.patient and e.patient.user else None
        staff_name = e.assigned_staff.full_name if e.assigned_staff else None

        return EscalationResponse(
            id=e.id,
            patient_id=e.patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            conversation_id=e.conversation_id,
            reason=e.reason,
            message=e.resolution_notes or f"Escalation for {e.reason.replace('_', ' ')}",
            status=e.status,
            priority=e.priority,
            assigned_to_user_id=e.assigned_to_user_id,
            assigned_to_name=staff_name,
            resolution_notes=e.resolution_notes,
            admin_notes=e.resolution_notes,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )

    @staticmethod
    def create_escalation(
        db: Session,
        patient_id: str,
        reason: str,
        priority: str = "medium",
        conversation_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> EscalationResponse:
        esc = Escalation(
            patient_id=patient_id,
            conversation_id=conversation_id,
            reason=reason,
            status="open",
            priority=priority,
            resolution_notes=notes,
        )
        db.add(esc)
        db.commit()
        db.refresh(esc)
        return EscalationService._format_escalation(esc)

    @staticmethod
    def get_patient_escalations(db: Session, patient_id: str) -> List[EscalationResponse]:
        escs = db.query(Escalation).filter(
            Escalation.patient_id == patient_id
        ).order_by(Escalation.created_at.desc()).all()
        return [EscalationService._format_escalation(e) for e in escs]

    @staticmethod
    def get_all_escalations(db: Session, status: Optional[str] = None, priority: Optional[str] = None) -> List[EscalationResponse]:
        query = db.query(Escalation)
        if status:
            query = query.filter(Escalation.status == status)
        if priority:
            query = query.filter(Escalation.priority == priority)
        escs = query.order_by(Escalation.created_at.desc()).all()
        return [EscalationService._format_escalation(e) for e in escs]

    @staticmethod
    def update_escalation(db: Session, escalation_id: str, data: EscalationUpdate) -> EscalationResponse:
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError("Escalation not found")

        if data.status:
            esc.status = data.status
        if data.priority:
            esc.priority = data.priority
        if data.assigned_to_user_id is not None:
            esc.assigned_to_user_id = data.assigned_to_user_id
        if data.resolution_notes:
            esc.resolution_notes = data.resolution_notes
        elif data.admin_notes:
            esc.resolution_notes = data.admin_notes

        db.commit()
        db.refresh(esc)
        return EscalationService._format_escalation(esc)


escalation_service = EscalationService()
