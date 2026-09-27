from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_number = Column(String(50), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    ambulance_type = Column(String(50), nullable=False, default="Basic Life Support (BLS)")  # BLS, ALS, Critical Care, Patient Transport
    status = Column(String(30), nullable=False, default="available", index=True)  # available, busy, offline, maintenance
    base_station = Column(String(255), nullable=False, default="ClinicCare Main Campus")
    current_location = Column(String(255), nullable=False, default="Main Base, Bay 1")
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(50), nullable=True)
    paramedic_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    requests = relationship("AmbulanceRequest", back_populates="ambulance")


class AmbulanceRequest(Base):
    __tablename__ = "ambulance_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    ambulance_id = Column(String(36), ForeignKey("ambulances.id", ondelete="SET NULL"), nullable=True, index=True)
    requester_name = Column(String(150), nullable=False)
    requester_phone = Column(String(50), nullable=False, index=True)
    pickup_address = Column(Text, nullable=False)
    destination_facility = Column(String(255), nullable=False, default="ClinicCare Multispeciality Hospital")
    emergency_priority = Column(String(30), nullable=False, default="high", index=True)  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="requested", index=True)  # requested, assigned, en_route, arrived, completed, cancelled
    notes = Column(Text, nullable=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient")
    ambulance = relationship("Ambulance", back_populates="requests")
