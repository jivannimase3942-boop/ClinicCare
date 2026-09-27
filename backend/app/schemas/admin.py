from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class MetricSummary(BaseModel):
    total_patients: int
    total_doctors: int
    today_appointments: int
    upcoming_appointments: int
    pending_appointments: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0
    pending_reports: int = 0
    open_escalations: int = 0
    active_ambulances: int = 0
    emergency_requests: int = 0
    available_blood_units: int = 0
    feedback_count: int = 0
    ai_conversations_count: int = 0
    average_rating: float = 0.0



class ChartDataPoint(BaseModel):
    label: str
    value: float


class AdminDashboardStats(BaseModel):
    metrics: MetricSummary
    appointments_by_day: List[ChartDataPoint]
    appointment_status_distribution: List[ChartDataPoint]
    feedback_ratings_distribution: List[ChartDataPoint]
    report_status_distribution: List[ChartDataPoint]
    ai_conversations_trend: List[ChartDataPoint]


class ErrorLogCreate(BaseModel):
    service_name: Optional[str] = "backend"
    error_level: Optional[str] = "ERROR"
    message: str
    stack_trace: Optional[str] = None
    endpoint: Optional[str] = None
    context_json: Optional[str] = None


class ErrorLogResponse(BaseModel):
    id: str
    service_name: str
    error_level: str
    message: str
    stack_trace: Optional[str] = None
    endpoint: Optional[str] = None
    context_json: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
