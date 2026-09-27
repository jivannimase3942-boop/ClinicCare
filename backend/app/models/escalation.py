from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(50), nullable=False)  # medical_question, emergency, billing, complaint, technical_issue, patient_requested_call, ai_uncertain, other
    status = Column(String(50), default="open", nullable=False, index=True)  # open, assigned, in_progress, resolved, closed
    priority = Column(String(20), default="medium", nullable=False, index=True)  # low, medium, high, emergency
    assigned_to_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("Patient", back_populates="escalations")
    conversation = relationship("AIConversation", back_populates="escalations")
    assigned_staff = relationship("User", foreign_keys=[assigned_to_user_id])
