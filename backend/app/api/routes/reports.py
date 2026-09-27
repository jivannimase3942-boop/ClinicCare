from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.report import ReportResponse
from app.services.report_service import report_service
from app.api.dependencies import get_current_patient, get_optional_patient
from app.models.user import Patient, User

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=ApiResponse[List[ReportResponse]])
@router.get("/my", response_model=ApiResponse[List[ReportResponse]])
def get_my_reports(
    patient_id: Optional[str] = Query(None, description="Optional patient ID"),
    phone: Optional[str] = Query(None, description="Optional patient phone"),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    target_patient_id = None
    if current_patient:
        target_patient_id = current_patient.id
    elif patient_id:
        target_patient_id = patient_id
    elif phone:
        user = db.query(User).filter(User.phone == phone).first()
        if user and user.patient_profile:
            target_patient_id = user.patient_profile.id
    else:
        first_patient = db.query(Patient).first()
        if first_patient:
            target_patient_id = first_patient.id

    if not target_patient_id:
        return ApiResponse(success=True, data=[])

    reports = report_service.get_patient_reports(db, target_patient_id)
    return ApiResponse(success=True, data=reports)


@router.get("/{id}", response_model=ApiResponse[ReportResponse])
def get_report(
    id: str,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    patient_id = current_patient.id if current_patient else None
    report = report_service.get_report_by_id(db, report_id=id, patient_id=patient_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found or unauthorized")
    return ApiResponse(success=True, data=report)
