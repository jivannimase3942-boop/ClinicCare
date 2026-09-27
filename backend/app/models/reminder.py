from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class FollowUpReminder(Base):
    __tablename__ = "follow_up_reminders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    reminder_type = Column(String(50), nullable=False, default="upcoming_appointment")  # upcoming_appointment, follow_up, pending_action, general
    scheduled_for = Column(DateTime, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(30), default="WhatsApp/SMS (Demo)", nullable=False)
    status = Column(String(30), default="scheduled", nullable=False, index=True)  # scheduled, pending, sent_demo, failed, cancelled
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient")
    appointment = relationship("Appointment")
    doctor = relationship("Doctor")
