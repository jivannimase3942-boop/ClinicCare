import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True, default="Bengaluru")
    state = Column(String(100), nullable=True, default="Karnataka")
    pincode = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="India")
    operating_hours = Column(String(255), nullable=False, default="09:00 AM - 08:00 PM (Monday - Saturday)")
    consultation_fee_default = Column(Numeric(10, 2), default=500.00, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    settings_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    users = relationship("User", back_populates="clinic")
    departments = relationship("Department", back_populates="clinic", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="clinic", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="clinic", cascade="all, delete-orphan")
