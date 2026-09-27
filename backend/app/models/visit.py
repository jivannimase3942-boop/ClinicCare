from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class VisitHistory(Base):
    __tablename__ = "visit_histories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    visit_date = Column(Date, nullable=False, index=True)
    visit_type = Column(String(50), default="OPD Consultation", nullable=False)  # OPD Consultation, Follow-up, Routine Checkup, Emergency
    visit_status = Column(String(30), default="completed", nullable=False)  # completed, in_progress, cancelled
    vitals_summary = Column(Text, nullable=True)  # e.g., "BP: 120/80 mmHg, Pulse: 72 bpm, SpO2: 99%"
    administrative_notes = Column(Text, nullable=True)  # e.g., "Registration fee cleared, consulting room Block A 101"
    follow_up_instructions = Column(Text, nullable=True)  # e.g., "Routine checkup in 2 weeks"
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient")
    doctor = relationship("Doctor")
    department = relationship("Department")
    appointment = relationship("Appointment")
