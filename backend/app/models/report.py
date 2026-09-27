from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)  # Blood Test, MRI, X-Ray, Pathology, ECG, etc.
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, processing, ready, delivered, failed
    file_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    report_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient", back_populates="reports")
    doctor = relationship("Doctor", back_populates="reports")
