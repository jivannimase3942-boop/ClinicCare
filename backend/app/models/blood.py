from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class BloodBank(Base):
    __tablename__ = "blood_banks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(150), nullable=True)
    operating_hours = Column(String(100), default="24/7 Emergency Service", nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    inventory = relationship("BloodInventory", back_populates="blood_bank", cascade="all, delete-orphan")


class BloodInventory(Base):
    __tablename__ = "blood_inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    blood_bank_id = Column(String(36), ForeignKey("blood_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    blood_group = Column(String(10), nullable=False, index=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    units_available = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="available", nullable=False)  # available, low_stock, critical_need
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    blood_bank = relationship("BloodBank", back_populates="inventory")


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_name = Column(String(150), nullable=False)
    blood_group = Column(String(10), nullable=False, index=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    units_required = Column(Integer, default=1, nullable=False)
    hospital_clinic_name = Column(String(200), nullable=False)
    location = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False, index=True)
    urgency = Column(String(30), default="urgent", nullable=False)  # normal, urgent, critical
    additional_info = Column(Text, nullable=True)
    status = Column(String(30), default="submitted", nullable=False, index=True)  # submitted, searching, match_found, fulfilled, cancelled
    matched_blood_bank_id = Column(String(36), ForeignKey("blood_banks.id", ondelete="SET NULL"), nullable=True)
    matched_bank_name = Column(String(200), nullable=True)
    admin_notes = Column(Text, nullable=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient")
    matched_bank = relationship("BloodBank")

