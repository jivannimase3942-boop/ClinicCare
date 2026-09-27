from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)
    facility_type = Column(String(100), nullable=False, default="Multispeciality Hospital")  # Hospital, Clinic, Trauma Center, Diagnostic Lab
    services = Column(Text, nullable=False)  # comma or json list of services
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    emergency_hotline = Column(String(50), nullable=False)
    operating_hours = Column(String(100), default="24/7 Emergency & Inpatient", nullable=False)
    is_emergency_ready = Column(Boolean, default=True, nullable=False)
    rating = Column(Numeric(2, 1), default=4.8, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
