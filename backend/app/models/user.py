import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, Text, Date
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True, index=True)
    role = Column(String(50), nullable=False, default="PATIENT", index=True)  # PATIENT, DOCTOR, ADMIN, FRONT_DESK
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="patient", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="patient", cascade="all, delete-orphan")
    conversations = relationship("AIConversation", back_populates="patient", cascade="all, delete-orphan")
    voice_calls = relationship("VoiceCallRequest", back_populates="patient", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="patient", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return self.user.full_name if self.user else "Patient"

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def phone(self) -> Optional[str]:
        return self.user.phone if self.user else None


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), default="Activity", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    doctors = relationship("Doctor", back_populates="department")
    appointments = relationship("Appointment", back_populates="department")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    specialization = Column(String(255), nullable=False)
    qualification = Column(String(255), nullable=False)
    experience_years = Column(Integer, default=0, nullable=False)
    consultation_fee = Column(Numeric(10, 2), default=0.00, nullable=False)
    location = Column(String(255), default="Main OPD, Room 101", nullable=False)
    available_days = Column(String(255), default="Monday,Tuesday,Wednesday,Thursday,Friday", nullable=False)
    available_hours_start = Column(String(10), default="09:00", nullable=False)
    available_hours_end = Column(String(10), default="17:00", nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    profile_image = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="doctor_profile")
    department = relationship("Department", back_populates="doctors")
    slots = relationship("DoctorSlot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")
    reports = relationship("Report", back_populates="doctor")

    @property
    def full_name(self) -> str:
        return self.user.full_name if self.user else "Doctor"

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def phone(self) -> Optional[str]:
        return self.user.phone if self.user else None


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
