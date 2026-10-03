import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base


class ABHAProfile(Base):
    """
    Ayushman Bharat Health Account (ABHA) profile linked to a patient.
    Stores verified 14-digit ABHA ID and ABHA address (health-id) without generating fake credentials.
    """
    __tablename__ = "abha_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    branch_id = Column(String(36), nullable=True, index=True)

    # ABHA Details
    abha_number = Column(String(30), nullable=True, index=True)  # e.g., "14-digit ABHA number"
    abha_address = Column(String(100), nullable=True, index=True)  # e.g., "username@abdm" or "user@sbx"
    verification_status = Column(String(30), default="NOT_LINKED", index=True)  # NOT_LINKED, PENDING_VERIFICATION, LINKED, REVOKED
    kyc_verified = Column(Boolean, default=False)
    auth_methods = Column(JSON, default=list)  # ["AADHAAR_OTP", "MOBILE_OTP", "DEMOGRAPHICS"]
    linked_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    # Metadata & references
    phr_address_alias = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", backref="abha_profile", uselist=False)


class ABDMConsentArtifact(Base):
    """
    Consent artifact representing electronic consent under ABDM Consent Manager (CM) architecture.
    """
    __tablename__ = "abdm_consent_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consent_request_id = Column(String(64), nullable=False, unique=True, index=True)
    consent_id = Column(String(64), nullable=True, index=True)
    
    tenant_id = Column(String(36), nullable=True, index=True)
    branch_id = Column(String(36), nullable=True, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    facility_hfr_id = Column(String(64), nullable=True, index=True)

    purpose_code = Column(String(30), default="CAREMGT")  # CAREMGT, BTG, PUBHLTH, RESRCH
    purpose_text = Column(String(255), default="Care Management")
    
    # Supported HI-Types in India: OPConsultation, Prescription, DiagnosticReport, DischargeSummary, ImmunizationRecord
    hi_types = Column(JSON, default=lambda: ["OPConsultation", "Prescription", "DiagnosticReport"])
    
    status = Column(String(30), default="REQUESTED", index=True)  # REQUESTED, GRANTED, DENIED, REVOKED, EXPIRED
    date_range_from = Column(DateTime, nullable=True)
    date_range_to = Column(DateTime, nullable=True)
    data_erase_at = Column(DateTime, nullable=True)
    signature = Column(Text, nullable=True)  # Digital signature from ABDM CM if available

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", backref="abdm_consents")
    requester = relationship("User")


class HealthInformationExchangeRecord(Base):
    """
    Audit and tracking of Health Information Provider (HIP) and Health Information User (HIU)
    data exchange transactions.
    """
    __tablename__ = "abdm_hie_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(64), nullable=False, unique=True, index=True)
    consent_artifact_id = Column(String(36), ForeignKey("abdm_consent_artifacts.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    tenant_id = Column(String(36), nullable=True, index=True)
    branch_id = Column(String(36), nullable=True, index=True)
    
    role_type = Column(String(10), default="HIP")  # HIP (Data Provider) or HIU (Data Consumer)
    record_type = Column(String(50), nullable=False)  # OPConsultation, DiagnosticReport, Prescription, DischargeSummary
    care_context_reference = Column(String(100), nullable=False)  # Episode or encounter ID
    
    transfer_status = Column(String(30), default="PENDING", index=True)  # PENDING, ENCRYPTED, TRANSFERRED, FAILED
    encryption_key_id = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    transferred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    consent_artifact = relationship("ABDMConsentArtifact", backref="hie_records")
    patient = relationship("Patient")


class FacilityRegistryProfile(Base):
    """
    Health Facility Registry (HFR) identifier and metadata for clinics and hospital branches.
    """
    __tablename__ = "abdm_facility_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, unique=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True)
    
    facility_name = Column(String(200), nullable=False)
    hfr_id = Column(String(64), nullable=True, unique=True, index=True)  # Official HFR ID e.g., "IN-MH-100452"
    facility_type = Column(String(50), default="HOSPITAL")  # HOSPITAL, CLINIC, DIAGNOSTIC_LAB, PHARMACY
    system_of_medicine = Column(String(50), default="ALLOPATHY")
    
    state_code = Column(String(10), nullable=True)  # e.g., "MH"
    district_code = Column(String(50), nullable=True)  # e.g., "Pune"
    pincode = Column(String(10), nullable=True)
    
    verification_status = Column(String(30), default="UNREGISTERED", index=True)  # UNREGISTERED, APPLIED, VERIFIED
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    branch = relationship("Branch", backref="hfr_profile")
    clinic = relationship("Clinic")


class ProfessionalRegistryProfile(Base):
    """
    Healthcare Professional Registry (HPR) identifier and credentials for registered medical doctors.
    """
    __tablename__ = "abdm_professional_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    hpr_id = Column(String(64), nullable=True, unique=True, index=True)  # e.g., "12-3456-7890-1234@hpr"
    registration_number = Column(String(64), nullable=True, index=True)  # State Medical Council Reg No
    state_medical_council = Column(String(150), nullable=True)  # e.g., "Maharashtra Medical Council"
    year_of_registration = Column(String(10), nullable=True)
    system_of_medicine = Column(String(50), default="ALLOPATHY")  # ALLOPATHY, AYUSH, DENTAL
    
    verification_status = Column(String(30), default="UNREGISTERED", index=True)  # UNREGISTERED, APPLIED, VERIFIED
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", backref="hpr_profile")
