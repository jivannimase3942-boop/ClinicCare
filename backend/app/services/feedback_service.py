from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.feedback import Feedback
from app.models.appointment import Appointment
from app.schemas.feedback import FeedbackCreate, FeedbackResponse


class FeedbackService:
    @staticmethod
    def _format_feedback(f: Feedback) -> FeedbackResponse:
        patient_name = f.patient.user.full_name if f.patient and f.patient.user else None
        doc_name = None
        if f.appointment and f.appointment.doctor and f.appointment.doctor.user:
            doc_name = f.appointment.doctor.user.full_name

        return FeedbackResponse(
            id=f.id,
            patient_id=f.patient_id,
            patient_name=patient_name,
            appointment_id=f.appointment_id,
            doctor_name=doc_name,
            rating=f.rating,
            comment=f.comment,
            status=f.status,
            created_at=f.created_at,
        )

    @staticmethod
    def submit_feedback(db: Session, patient_id: str, data: FeedbackCreate) -> FeedbackResponse:
        if data.appointment_id:
            # Check if appointment belongs to this patient
            app = db.query(Appointment).filter(
                Appointment.id == data.appointment_id,
                Appointment.patient_id == patient_id
            ).first()
            if not app:
                raise ValueError("Appointment not found or unauthorized")

            # Check if feedback already submitted for this appointment
            existing = db.query(Feedback).filter(Feedback.appointment_id == data.appointment_id).first()
            if existing:
                raise ValueError("Feedback already submitted for this appointment")

        feedback = Feedback(
            patient_id=patient_id,
            appointment_id=data.appointment_id,
            rating=data.rating,
            comment=data.comment,
            status="active",
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return FeedbackService._format_feedback(feedback)

    @staticmethod
    def get_patient_feedbacks(db: Session, patient_id: str) -> List[FeedbackResponse]:
        feedbacks = db.query(Feedback).filter(
            Feedback.patient_id == patient_id
        ).order_by(Feedback.created_at.desc()).all()
        return [FeedbackService._format_feedback(f) for f in feedbacks]

    @staticmethod
    def get_all_feedbacks(db: Session, rating_filter: Optional[int] = None) -> List[FeedbackResponse]:
        query = db.query(Feedback)
        if rating_filter:
            query = query.filter(Feedback.rating == rating_filter)
        feedbacks = query.order_by(Feedback.created_at.desc()).all()
        return [FeedbackService._format_feedback(f) for f in feedbacks]



    @staticmethod
    def scan_and_send_feedback_requests(db: Session) -> dict:
        """Scans completed appointments without feedback and dispatches WhatsApp feedback requests (1-5 rating)."""
        import asyncio
        from app.integrations.whatsapp.service import whatsapp_service
        from app.core.config import settings

        completed = db.query(Appointment).filter(
            Appointment.status == "completed"
        ).outerjoin(Feedback, Appointment.id == Feedback.appointment_id).filter(
            Feedback.id == None
        ).all()

        results = []
        for app in completed:
            phone = app.patient.user.phone if app.patient and app.patient.user else None
            patient_name = app.patient.user.full_name if app.patient and app.patient.user else "Patient"
            doctor_name = app.doctor.user.full_name if app.doctor and app.doctor.user else "your doctor"

            if phone:
                msg = (
                    f"Hi {patient_name}, thank you for your consultation with Dr. {doctor_name} at {settings.HOSPITAL_NAME}. "
                    f"How would you rate your experience today? Please reply with a rating from 1 (Poor) to 5 (Excellent), "
                    f"followed by any comments."
                )
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            res = pool.submit(asyncio.run, whatsapp_service.send_text_message(phone, msg)).result()
                    else:
                        res = asyncio.run(whatsapp_service.send_text_message(phone, msg))
                except Exception:
                    res = {"status": "dispatched", "simulated": True}
                results.append({"appointment_id": app.id, "phone": phone, "result": res})

        return {"scanned": len(completed), "feedback_requests_sent": len(results), "details": results}

feedback_service = FeedbackService()
