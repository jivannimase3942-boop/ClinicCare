from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class DoctorSlot(Base):
    __tablename__ = "doctor_slots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_doctor_slot_time"),
    )

    doctor = relationship("Doctor", back_populates="slots")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(String(10), nullable=False, index=True)
    status = Column(String(50), default="confirmed", nullable=False, index=True)  # confirmed, pending, checked_in, in_consultation, completed, cancelled, rescheduled, no_show
    appointment_type = Column(String(50), default="NEW_CONSULTATION", nullable=False, index=True)  # NEW_CONSULTATION, FOLLOW_UP, PROCEDURE, TELECONSULTATION, EMERGENCY, HOME_VISIT
    token_number = Column(String(20), nullable=True, index=True)
    queue_status = Column(String(30), default="NOT_QUEUED", nullable=False, index=True)  # NOT_QUEUED, WAITING, CALLED, IN_CONSULTATION, COMPLETED, SKIPPED, CANCELLED
    checked_in_at = Column(DateTime, nullable=True)
    consultation_started_at = Column(DateTime, nullable=True)
    consultation_ended_at = Column(DateTime, nullable=True)
    is_walk_in = Column(Boolean, default=False, nullable=False)
    parent_appointment_id = Column(String(36), nullable=True)
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    cancelled_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    department = relationship("Department", back_populates="appointments")
    feedback = relationship("Feedback", back_populates="appointment", uselist=False)


class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    doctor = relationship("Doctor", back_populates="leaves")


class AppointmentWaitlist(Base):
    __tablename__ = "appointment_waitlists"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    desired_date = Column(Date, nullable=False, index=True)
    preferred_time_range = Column(String(50), nullable=True)  # e.g., "Morning", "Afternoon", "Evening"
    status = Column(String(30), default="WAITING", nullable=False, index=True)  # WAITING, OFFERED, BOOKED, EXPIRED, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    patient = relationship("Patient")
    doctor = relationship("Doctor", back_populates="waitlists")

