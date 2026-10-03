from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Organization(Base):
    """
    Enterprise Healthcare Organization (e.g., Hospital Chain, Polyclinic Network).
    Governs multiple branches/clinics under a centralized hierarchy.
    """
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    headquarters_address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    branches = relationship("Branch", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", foreign_keys="User.organization_id", back_populates="organization")


class Branch(Base):
    """
    Physical facility / operational branch belonging to an Organization.
    Directly maps to the Clinic tenant model for existing workflow preservation.
    """
    __tablename__ = "branches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), default="Bengaluru", nullable=False)
    state = Column(String(100), default="Karnataka", nullable=False)
    pincode = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    operating_hours = Column(String(255), default="08:00 AM - 09:00 PM (Mon-Sat)", nullable=False)
    branch_admin_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL", use_alter=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="branches")
    clinic = relationship("Clinic")
    branch_admin = relationship("User", foreign_keys=[branch_admin_user_id])
    users = relationship("User", foreign_keys="User.branch_id", back_populates="branch")
