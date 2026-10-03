from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Date as SqlDate
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class ConsultationRecord(Base):
    """
    Longitudinal clinical consultation record created and supervised by doctors.
    Maintains draft/finalized workflow and immutable version history once finalized.
    """
    __tablename__ = "consultation_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status: DRAFT, FINALIZED, AMENDED
    status = Column(String(20), default="DRAFT", nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)

    # Clinical fields
    chief_complaint = Column(Text, nullable=False)
    history_of_present_illness = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    lifestyle_notes = Column(Text, nullable=True)
    examination_notes = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=False)
    treatment_plan = Column(Text, nullable=True)
    investigations_ordered = Column(Text, nullable=True)
    follow_up_date = Column(SqlDate, nullable=True)
    referral = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)

    # Finalization & Supervision
    is_finalized = Column(Boolean, default=False, nullable=False)
    finalized_at = Column(DateTime, nullable=True)
    finalized_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    clinic = relationship("Clinic")
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    appointment = relationship("Appointment")
    vitals = relationship("VitalSign", back_populates="consultation", cascade="all, delete-orphan")


class VitalSign(Base):
    """
    Structured patient vital signs recorded by clinical staff or during consultation.
    """
    __tablename__ = "vital_signs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    consultation_id = Column(String(36), ForeignKey("consultation_records.id", ondelete="SET NULL"), nullable=True, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    temperature_celsius = Column(Float, nullable=True)
    pulse_bpm = Column(Integer, nullable=True)
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    spo2_percent = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    recorded_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    clinic = relationship("Clinic")
    patient = relationship("Patient")
    consultation = relationship("ConsultationRecord", back_populates="vitals")
    recorded_by = relationship("User")


class ClinicalDocument(Base):
    """
    Secure clinical attachments and document metadata.
    Private access strictly governed by RBAC and tenant authorization.
    """
    __tablename__ = "clinical_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    consultation_id = Column(String(36), ForeignKey("consultation_records.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    document_type = Column(String(50), nullable=False)  # CONSULTATION_SUMMARY, REFERRAL_LETTER, MEDICAL_CERTIFICATE, ATTACHMENT
    title = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_type = Column(String(50), default="application/pdf", nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    clinic = relationship("Clinic")
    patient = relationship("Patient")
    consultation = relationship("ConsultationRecord")
    uploaded_by = relationship("User")
