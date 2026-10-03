from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


# Association table for LabOrder and LabTest catalog items
lab_order_tests = Table(
    "lab_order_tests",
    Base.metadata,
    Column("order_id", String(36), ForeignKey("lab_orders.id", ondelete="CASCADE"), primary_key=True),
    Column("test_id", String(36), ForeignKey("lab_tests.id", ondelete="RESTRICT"), primary_key=True),
)


class LabTest(Base):
    """
    Laboratory diagnostic test catalog.
    Configurable per clinic or available system-wide.
    """
    __tablename__ = "lab_tests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)  # e.g., CBC, LIPID, LFT, KFT, HBA1C
    category = Column(String(100), default="BIOCHEMISTRY", nullable=False)  # HEMATOLOGY, BIOCHEMISTRY, MICROBIOLOGY, PATHOLOGY
    sample_type = Column(String(100), default="Whole Blood", nullable=False)  # Whole Blood, Serum, Plasma, Urine, Sputum
    turnaround_hours = Column(Integer, default=24, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    normal_range = Column(String(255), nullable=True)  # e.g., "70 - 99 mg/dL"
    unit = Column(String(50), nullable=True)  # e.g., "mg/dL", "g/dL", "%"
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")


class LabOrder(Base):
    """
    Laboratory investigation order issued by doctor or triage.
    """
    __tablename__ = "lab_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    priority = Column(String(20), default="ROUTINE", nullable=False)  # ROUTINE, URGENT, STAT
    status = Column(String(30), default="ORDERED", nullable=False, index=True)
    # Lifecycle: ORDERED -> SAMPLE_PENDING -> SAMPLE_COLLECTED -> PROCESSING -> RESULT_READY -> VALIDATED -> CANCELLED

    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    appointment = relationship("Appointment")
    tests = relationship("LabTest", secondary=lab_order_tests)
    samples = relationship("LabSample", back_populates="order", cascade="all, delete-orphan")
    results = relationship("LabResult", back_populates="order", cascade="all, delete-orphan")
    report = relationship("LabReport", back_populates="order", uselist=False, cascade="all, delete-orphan")


class LabSample(Base):
    """
    Specimen sample tracking with barcode identification.
    """
    __tablename__ = "lab_samples"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lab_order_id = Column(String(36), ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True)

    barcode_number = Column(String(50), unique=True, nullable=False, index=True)
    sample_type = Column(String(100), nullable=False)  # Whole Blood, Serum, Urine
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, COLLECTED, REJECTED, PROCESSED
    rejection_reason = Column(String(255), nullable=True)
    collected_at = Column(DateTime, nullable=True)
    collected_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("LabOrder", back_populates="samples")
    collector = relationship("User")


class LabResult(Base):
    """
    Quantitative or qualitative test parameter result with reference range and abnormal flag.
    """
    __tablename__ = "lab_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lab_order_id = Column(String(36), ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_test_id = Column(String(36), ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False, index=True)

    parameter_name = Column(String(150), nullable=False)
    result_value = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(150), nullable=True)
    is_abnormal = Column(Boolean, default=False, nullable=False)
    technician_notes = Column(Text, nullable=True)
    tested_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("LabOrder", back_populates="results")
    test = relationship("LabTest")
    technician = relationship("User")


class LabReport(Base):
    """
    Final pathologist-validated diagnostic laboratory report.
    Only released reports are visible to patients.
    """
    __tablename__ = "lab_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_order_id = Column(String(36), ForeignKey("lab_orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    report_number = Column(String(50), unique=True, nullable=False, index=True)
    is_validated = Column(Boolean, default=False, nullable=False)
    validated_at = Column(DateTime, nullable=True)
    validated_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    is_released = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime, nullable=True)
    summary_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")
    order = relationship("LabOrder", back_populates="report")
    patient = relationship("Patient")
    validator = relationship("User")
