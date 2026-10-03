from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.api.dependencies import require_roles, get_current_user
from app.models.user import User, Patient, Doctor, Department
from app.models.escalation import Escalation
from app.models.ambulance import Ambulance, AmbulanceRequest
from app.models.blood import BloodBank, BloodInventory
from app.models.facility import Facility
from app.models.visit import VisitHistory
from app.models.reminder import FollowUpReminder
from app.services.admin_service import admin_service
from app.services.doctor_service import doctor_service
from app.services.appointment_service import appointment_service
from app.services.report_service import report_service
from app.services.feedback_service import feedback_service
from app.services.escalation_service import escalation_service
from app.services.voice_service import voice_service
from app.ai.service import ai_service
from app.services.ambulance_service import ambulance_service
from app.services.blood_service import blood_service
from app.services.facility_service import facility_service
from app.services.patient_service import patient_service
from app.services.reminder_service import reminder_service
from app.services.emergency_service import emergency_service
from app.services.audit_service import audit_service
from app.services.clinic_service import clinic_service
from app.schemas.admin import AdminDashboardStats, ErrorLogResponse, ErrorLogCreate
from app.schemas.doctor import DoctorResponse, DepartmentResponse, DepartmentCreate, DoctorCreate
from app.schemas.appointment import AppointmentResponse, AppointmentStatusUpdate
from app.schemas.report import ReportResponse, ReportCreate, ReportUpdateStatus
from app.schemas.feedback import FeedbackResponse
from app.schemas.escalation import EscalationResponse, EscalationUpdate
from app.schemas.voice import VoiceCallResponse, VoiceCallUpdateStatus
from app.schemas.ai import AIConversationResponse
from app.schemas.ambulance import AmbulanceResponse, AmbulanceRequestResponse, AmbulanceAssignPayload
from app.schemas.blood import BloodInventoryItem, BloodGroupSearchResult
from app.schemas.facility import FacilityResponse
from app.schemas.patient import PatientProfileResponse, VisitHistoryResponse
from app.schemas.reminder import FollowUpReminderResponse
from app.schemas.emergency import EmergencyRequestResponse, EmergencyStatsResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard & Management"])
admin_auth = Depends(require_roles(["ADMIN", "FRONT_DESK"]))
strict_admin_auth = Depends(require_roles(["ADMIN"]))



@router.get("/stats", response_model=ApiResponse[AdminDashboardStats], dependencies=[admin_auth])
def get_stats(db: Session = Depends(get_db)):
    stats = admin_service.get_dashboard_stats(db)
    return ApiResponse(success=True, data=stats)


@router.get("/patients", response_model=ApiResponse[List[Dict[str, Any]]], dependencies=[admin_auth])
def list_patients(search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Patient).join(User, Patient.user_id == User.id)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(User.full_name.ilike(s) | User.email.ilike(s) | User.phone.ilike(s))
    patients = query.order_by(Patient.created_at.desc()).all()
    data = [
        {
            "id": p.id,
            "user_id": p.user_id,
            "full_name": p.user.full_name,
            "email": p.user.email,
            "phone": p.user.phone,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "emergency_contact": p.emergency_contact,
            "created_at": p.created_at.isoformat(),
        }
        for p in patients
    ]
    return ApiResponse(success=True, data=data)


@router.get("/doctors", response_model=ApiResponse[List[DoctorResponse]], dependencies=[admin_auth])
def list_admin_doctors(db: Session = Depends(get_db)):
    docs = doctor_service.get_doctors(db, active_only=False)
    return ApiResponse(success=True, data=docs)


@router.post("/departments", response_model=ApiResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED, dependencies=[admin_auth])
def create_dept(data: DepartmentCreate, db: Session = Depends(get_db)):
    dept = doctor_service.create_department(db, name=data.name, description=data.description, icon=data.icon)
    return ApiResponse(success=True, message="Department created", data=DepartmentResponse.model_validate(dept))


@router.get("/pending-staff", response_model=ApiResponse[List[Dict[str, Any]]], dependencies=[strict_admin_auth])
def list_pending_staff(db: Session = Depends(get_db)):
    pending_users = db.query(User).filter(User.role.in_(["PENDING_DOCTOR", "PENDING_FRONT_DESK"])).all()
    data = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "specialization": u.doctor_profile.specialization if u.doctor_profile else None,
            "qualification": u.doctor_profile.qualification if u.doctor_profile else None,
        }
        for u in pending_users
    ]
    return ApiResponse(success=True, data=data)


@router.post("/approve-staff/{user_id}", response_model=ApiResponse[Dict[str, Any]], dependencies=[strict_admin_auth])
def approve_staff(
    user_id: str,
    new_role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    resolved_role = new_role or ("DOCTOR" if user.role == "PENDING_DOCTOR" else "FRONT_DESK")
    try:
        from app.services.auth_service import auth_service
        approved = auth_service.approve_pending_staff(db, user_id, resolved_role)
        audit_service.log_action(
            db=db,
            action="STAFF_APPROVED",
            user=current_user,
            clinic_id=current_user.clinic_id,
            entity_type="User",
            entity_id=approved.id,
            details={"approved_email": approved.email, "assigned_role": approved.role}
        )
        return ApiResponse(
            success=True,
            message=f"Staff account approved. Role set to {approved.role}.",
            data={"id": approved.id, "email": approved.email, "role": approved.role}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/appointments", response_model=ApiResponse[List[AppointmentResponse]], dependencies=[admin_auth])
def list_admin_appointments(
    doctor_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db)
):
    apps = appointment_service.get_all_appointments(
        db, doctor_id=doctor_id, patient_id=patient_id, status=status_filter, date_filter=date_filter
    )
    return ApiResponse(success=True, data=apps)


@router.patch("/appointments/{id}/status", response_model=ApiResponse[AppointmentResponse], dependencies=[admin_auth])
def update_appointment_status(
    id: str,
    data: Optional[AppointmentStatusUpdate] = Body(None),
    status_param: Optional[str] = Query(None, alias="status", description="confirmed, completed, cancelled, no_show"),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    target_status = (data.status if data and data.status else status_param)
    target_notes = (data.notes if data and data.notes is not None else notes)
    if not target_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")

    try:
        app = appointment_service.update_appointment_status(db, id, target_status, target_notes)
        return ApiResponse(success=True, message="Appointment status updated", data=app)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/reports", response_model=ApiResponse[List[ReportResponse]], dependencies=[admin_auth])
def list_admin_reports(status: Optional[str] = None, db: Session = Depends(get_db)):
    reports = report_service.get_all_reports(db, status=status)
    return ApiResponse(success=True, data=reports)


@router.post("/reports", response_model=ApiResponse[ReportResponse], status_code=status.HTTP_201_CREATED, dependencies=[admin_auth])
def create_report(data: ReportCreate, db: Session = Depends(get_db)):
    rep = report_service.create_report(db, data)
    return ApiResponse(success=True, message="Report created", data=rep)


@router.patch("/reports/{id}/status", response_model=ApiResponse[ReportResponse], dependencies=[admin_auth])
def update_report_status(id: str, data: ReportUpdateStatus, db: Session = Depends(get_db)):
    try:
        rep = report_service.update_report_status(db, id, data)
        return ApiResponse(success=True, message="Report status updated", data=rep)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/feedback", response_model=ApiResponse[List[FeedbackResponse]], dependencies=[admin_auth])
def list_admin_feedback(rating: Optional[int] = None, db: Session = Depends(get_db)):
    fbs = feedback_service.get_all_feedbacks(db, rating_filter=rating)
    return ApiResponse(success=True, data=fbs)


@router.get("/escalations", response_model=ApiResponse[List[EscalationResponse]], dependencies=[admin_auth])
def list_admin_escalations(status: Optional[str] = None, priority: Optional[str] = None, db: Session = Depends(get_db)):
    escs = escalation_service.get_all_escalations(db, status=status, priority=priority)
    return ApiResponse(success=True, data=escs)


@router.patch("/escalations/{id}", response_model=ApiResponse[EscalationResponse], dependencies=[admin_auth])
def update_admin_escalation(id: str, data: EscalationUpdate, db: Session = Depends(get_db)):
    try:
        esc = escalation_service.update_escalation(db, id, data)
        return ApiResponse(success=True, message="Escalation updated", data=esc)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/voice-calls", response_model=ApiResponse[List[VoiceCallResponse]], dependencies=[admin_auth])
def list_admin_voice_calls(status: Optional[str] = None, db: Session = Depends(get_db)):
    calls = voice_service.get_all_voice_calls(db, status=status)
    return ApiResponse(success=True, data=calls)


@router.patch("/voice-calls/{id}", response_model=ApiResponse[VoiceCallResponse], dependencies=[admin_auth])
def update_admin_voice_call(id: str, data: VoiceCallUpdateStatus, db: Session = Depends(get_db)):
    try:
        call = voice_service.update_voice_status(db, id, data)
        return ApiResponse(success=True, message="Voice call updated", data=call)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/conversations", response_model=ApiResponse[List[AIConversationResponse]], dependencies=[strict_admin_auth])
def list_admin_conversations(limit: int = 50, db: Session = Depends(get_db)):
    convs = ai_service.get_all_conversations(db, limit=limit)
    return ApiResponse(success=True, data=convs)


@router.get("/errors", response_model=ApiResponse[List[ErrorLogResponse]], dependencies=[strict_admin_auth])
def list_admin_errors(limit: int = 50, db: Session = Depends(get_db)):
    logs = admin_service.get_error_logs(db, limit=limit)
    return ApiResponse(success=True, data=logs)


@router.post("/errors", response_model=ApiResponse[ErrorLogResponse], status_code=status.HTTP_201_CREATED, dependencies=[strict_admin_auth])
def create_admin_error(data: ErrorLogCreate, db: Session = Depends(get_db)):
    log = admin_service.create_error_log(
        db=db,
        service_name=data.service_name,
        error_level=data.error_level,
        message=data.message,
        stack_trace=data.stack_trace,
        endpoint=data.endpoint,
        context_json=data.context_json,
    )
    return ApiResponse(success=True, message="Error logged successfully", data=ErrorLogResponse.model_validate(log))


@router.post("/tasks/scan-reminders", response_model=ApiResponse[Dict[str, Any]], dependencies=[strict_admin_auth])
def trigger_scan_reminders(db: Session = Depends(get_db)):
    result = appointment_service.scan_and_send_reminders(db)
    return ApiResponse(success=True, message="Reminders scan completed", data=result)


@router.post("/tasks/scan-feedback", response_model=ApiResponse[Dict[str, Any]], dependencies=[strict_admin_auth])
def trigger_scan_feedback(db: Session = Depends(get_db)):
    result = feedback_service.scan_and_send_feedback_requests(db)
    return ApiResponse(success=True, message="Feedback scan completed", data=result)


@router.post("/tasks/scan-reports", response_model=ApiResponse[Dict[str, Any]], dependencies=[strict_admin_auth])
def trigger_scan_reports(db: Session = Depends(get_db)):
    result = report_service.scan_and_send_report_notifications(db)
    return ApiResponse(success=True, message="Reports scan completed", data=result)


@router.get("/audit-logs", response_model=ApiResponse[List[Dict[str, Any]]], dependencies=[strict_admin_auth])
def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Enforce clinic tenant isolation: clinic admins only see their own clinic logs unless SUPER_ADMIN
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    logs = audit_service.get_logs(
        db=db,
        clinic_id=clinic_filter,
        action=action,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    data = [
        {
            "id": l.id,
            "clinic_id": l.clinic_id,
            "user_id": l.user_id,
            "user_email": l.user_email,
            "user_role": l.user_role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
    return ApiResponse(success=True, data=data)


