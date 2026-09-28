from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.report import ReportResponse
from app.services.report_service import report_service
from app.api.dependencies import get_current_user, get_optional_user
from app.models.user import Patient, User

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=ApiResponse[List[ReportResponse]])
@router.get("/my", response_model=ApiResponse[List[ReportResponse]])
def get_my_reports(
    patient_id: Optional[str] = Query(None, description="Optional patient ID"),
    phone: Optional[str] = Query(None, description="Optional patient phone"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if current_user and current_user.role == "PATIENT":
        # Strict patient privacy: ignore external patient_id and only return own reports
        if not current_user.patient_profile:
            return ApiResponse(success=True, data=[])
        reports = report_service.get_patient_reports(db, current_user.patient_profile.id)
        return ApiResponse(success=True, data=reports)

    if current_user and current_user.role in ["ADMIN", "FRONT_DESK", "DOCTOR"]:
        target_pid = patient_id
        if not target_pid and phone:
            u = db.query(User).filter(User.phone == phone).first()
            if u and u.patient_profile:
                target_pid = u.patient_profile.id
        if target_pid:
            reports = report_service.get_patient_reports(db, target_pid)
        else:
            reports = report_service.get_all_reports(db)
        return ApiResponse(success=True, data=reports)

    # Automated integration calls with specific patient_id
    if patient_id:
        reports = report_service.get_patient_reports(db, patient_id)
        return ApiResponse(success=True, data=reports)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to view reports")


@router.get("/{id}", response_model=ApiResponse[ReportResponse])
def get_report(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    report = report_service.get_report_by_id(db, report_id=id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Patient privacy check: Patient can only view their own medical report
    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or report.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's medical report")

    return ApiResponse(success=True, data=report)
