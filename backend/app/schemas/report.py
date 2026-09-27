from typing import Optional, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    title: str
    report_type: str
    status: str = "pending"
    file_url: Optional[str] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    report_date: Optional[date] = None

    def model_post_init(self, __context: Any) -> None:
        if self.report_date is None:
            self.report_date = date.today()
        if self.notes is None and self.summary is not None:
            self.notes = self.summary
        elif self.summary is None and self.notes is not None:
            self.summary = self.notes


class ReportUpdateStatus(BaseModel):
    status: str
    notes: Optional[str] = None
    summary: Optional[str] = None
    file_url: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.notes is None and self.summary is not None:
            self.notes = self.summary
        elif self.summary is None and self.notes is not None:
            self.summary = self.notes


class ReportResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    title: str
    report_type: str
    status: str
    file_url: Optional[str] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    report_date: date
    created_at: datetime
    updated_at: datetime

    def model_post_init(self, __context: Any) -> None:
        if self.summary is None and self.notes is not None:
            self.summary = self.notes
        elif self.notes is None and self.summary is not None:
            self.notes = self.summary

    model_config = {"from_attributes": True}

