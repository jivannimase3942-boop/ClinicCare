from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.reminder import FollowUpReminder
from app.models.appointment import Appointment
from app.models.user import Patient, User
from app.schemas.reminder import FollowUpReminderResponse, FollowUpReminderCreate


class ReminderService:
    @staticmethod
    def _format_reminder(r: FollowUpReminder) -> FollowUpReminderResponse:
        pat_name = r.patient.user.full_name if r.patient and r.patient.user else None
        pat_phone = r.patient.user.phone if r.patient and r.patient.user else None
        doc_name = r.doctor.user.full_name if r.doctor and r.doctor.user else None

        return FollowUpReminderResponse(
            id=r.id,
            patient_id=r.patient_id,
            patient_name=pat_name,
            patient_phone=pat_phone,
            appointment_id=r.appointment_id,
            doctor_id=r.doctor_id,
            doctor_name=doc_name,
            reminder_type=r.reminder_type,
            scheduled_for=r.scheduled_for,
            title=r.title,
            message=r.message,
            channel=r.channel,
            status=r.status,
            sent_at=r.sent_at,
            created_at=r.created_at,
        )

    @staticmethod
    def get_reminders(
        db: Session,
        patient_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[FollowUpReminderResponse]:
        query = db.query(FollowUpReminder)
        if patient_id:
            query = query.filter(FollowUpReminder.patient_id == patient_id)
        if status:
            query = query.filter(FollowUpReminder.status == status)
        reminders = query.order_by(FollowUpReminder.scheduled_for.desc()).all()
        return [ReminderService._format_reminder(r) for r in reminders]

    @staticmethod
    def create_reminder(
        db: Session,
        data: FollowUpReminderCreate
    ) -> FollowUpReminderResponse:
        rem = FollowUpReminder(
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            doctor_id=data.doctor_id,
            reminder_type=data.reminder_type or "upcoming_appointment",
            scheduled_for=data.scheduled_for,
            title=data.title,
            message=data.message,
            channel=data.channel or "WhatsApp/SMS (Demo)",
            status="scheduled",
        )
        db.add(rem)
        db.commit()
        db.refresh(rem)
        return ReminderService._format_reminder(rem)

    @staticmethod
    def trigger_simulated_dispatch(
        db: Session,
        reminder_id: str
    ) -> FollowUpReminderResponse:
        rem = db.query(FollowUpReminder).filter(FollowUpReminder.id == reminder_id).first()
        if not rem:
            raise ValueError("Reminder not found")
        rem.status = "sent_demo"
        rem.sent_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rem)
        return ReminderService._format_reminder(rem)


reminder_service = ReminderService()
