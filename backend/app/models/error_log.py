from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    service_name = Column(String(100), default="backend", nullable=False)
    error_level = Column(String(20), default="ERROR", nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    context_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
