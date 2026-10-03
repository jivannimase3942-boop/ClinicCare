from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Date as SqlDate
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Medicine(Base):
    """
    Pharmacy-ready Medicine Master catalog.
    Configurable per clinic tenant or hospital system.
    """
    __tablename__ = "medicines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True, index=True)

    brand_name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), nullable=False, index=True)
    strength = Column(String(100), nullable=False)  # e.g., "500 mg", "10 mg/ml"
    dosage_form = Column(String(50), default="TABLET", nullable=False)  # TABLET, CAPSULE, SYRUP, INJECTION, DROPS, OINTMENT
    manufacturer = Column(String(255), nullable=True)
    category = Column(String(100), default="GENERAL", nullable=False)  # ANTIBIOTIC, ANALGESIC, ANTIHYPERTENSIVE, etc.
    hsn_code = Column(String(20), default="3004", nullable=True)
    gst_rate_percent = Column(Float, default=12.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")


class Prescription(Base):
    """
    Digital Prescription governed strictly by human physician review and signature.
    AI may assist with drafting, but final issuance requires physician authorization.
    """
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    consultation_id = Column(String(36), ForeignKey("consultation_records.id", ondelete="SET NULL"), nullable=True, index=True)

    prescription_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="DRAFT", nullable=False, index=True)  # DRAFT, FINALIZED, ISSUED, CANCELLED

    diagnosis_summary = Column(Text, nullable=False)
    general_advice = Column(Text, nullable=True)
    diet_lifestyle_notes = Column(Text, nullable=True)
    follow_up_date = Column(SqlDate, nullable=True)

    # Supervision & Verification
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
    consultation = relationship("ConsultationRecord")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionItem(Base):
    """
    Individual medication item within a digital prescription.
    """
    __tablename__ = "prescription_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(String(36), ForeignKey("medicines.id", ondelete="SET NULL"), nullable=True)

    medicine_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    dosage_form = Column(String(50), default="TABLET", nullable=False)
    strength = Column(String(100), nullable=True)
    dosage = Column(String(100), nullable=False)  # e.g., "1 tablet", "5 ml"
    frequency = Column(String(100), nullable=False)  # e.g., "1-0-1 (Twice daily)", "SOS"
    duration = Column(String(100), nullable=False)  # e.g., "5 days", "1 month"
    route = Column(String(50), default="ORAL", nullable=False)  # ORAL, TOPICAL, INHALATION, IV
    instructions = Column(String(255), default="After food", nullable=False)  # After food, Before food
    quantity = Column(Integer, default=10, nullable=False)

    prescription = relationship("Prescription", back_populates="items")
    medicine = relationship("Medicine")
