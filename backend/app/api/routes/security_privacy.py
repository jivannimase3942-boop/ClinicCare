import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.security_privacy import (
    UserSessionResponse,
    SecurityEventResponse,
    PasswordChangeRequest,
    StaffStatusUpdateRequest,
    PatientConsentCreate,
    PatientConsentWithdraw,
    PatientConsentResponse,
    PrivacyRequestCreate,
    PrivacyRequestProcess,
    PrivacyRequestResponse,
    MFASetupRequest,
    MFAResponse,
)
from app.models.user import User
from app.services.security_privacy_service import security_privacy_service
from app.api.dependencies import get_current_user, require_roles


router = APIRouter(prefix="", tags=["Security, Privacy & Consent"])


# -------------------------------------------------------------
# 1. Active Sessions & Session Controls
# -------------------------------------------------------------

@router.get("/security/sessions", response_model=ApiResponse[List[UserSessionResponse]])
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = security_privacy_service.get_active_sessions(db, current_user.id)
    resp = [
        UserSessionResponse(
            id=s.id,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            device_info=s.device_info,
            is_active=s.is_active,
            last_activity_at=s.last_activity_at,
            expires_at=s.expires_at,
            created_at=s.created_at,
            is_current=True if s.token_jti == getattr(current_user, "current_jti", None) else False,
        )
        for s in sessions
    ]
    return ApiResponse(success=True, message="Active sessions retrieved", data=resp)


@router.post("/security/sessions/logout-current", response_model=ApiResponse[dict])
def logout_current_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_jti = getattr(current_user, "current_jti", None)
    if current_jti:
        security_privacy_service.revoke_session(db, current_user.id, current_jti)
    security_privacy_service.record_security_event(
        db=db,
        event_type="LOGOUT",
        user_id=current_user.id,
        user_email=current_user.email,
        clinic_id=current_user.clinic_id,
        severity="INFO",
        details="User logged out of current active session",
    )
    return ApiResponse(success=True, message="Current session successfully terminated", data={"status": "revoked"})


@router.post("/security/sessions/logout-all", response_model=ApiResponse[dict])
def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = security_privacy_service.revoke_all_sessions(db, current_user.id)
    security_privacy_service.record_security_event(
        db=db,
        event_type="LOGOUT_ALL",
        user_id=current_user.id,
        user_email=current_user.email,
        clinic_id=current_user.clinic_id,
        severity="INFO",
        details=f"All {count} active sessions revoked by user request",
    )
    return ApiResponse(success=True, message=f"Successfully terminated {count} active sessions", data={"revoked_count": count})


# -------------------------------------------------------------
# 2. Security Events Audit
# -------------------------------------------------------------

@router.get("/security/events", response_model=ApiResponse[List[SecurityEventResponse]])
def list_security_events(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role in ["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"]:
        # Enterprise oversight: clinic-scoped or global
        events = security_privacy_service.list_security_events(
            db, clinic_id=current_user.clinic_id if current_user.role == "ADMIN" else None, limit=limit, offset=offset
        )
    else:
        # Regular users strictly restricted to their own security events
        events = security_privacy_service.list_security_events(db, user_id=current_user.id, limit=limit, offset=offset)

    resp = [SecurityEventResponse.model_validate(e) for e in events]
    return ApiResponse(success=True, message="Security events retrieved", data=resp)


# -------------------------------------------------------------
# 3. Password Change & Staff Management
# -------------------------------------------------------------

@router.post("/security/change-password", response_model=ApiResponse[dict])
def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        security_privacy_service.change_password(
            db=db,
            user=current_user,
            old_password=payload.old_password,
            new_password=payload.new_password,
            ip_address=ip,
            user_agent=ua,
        )
        return ApiResponse(
            success=True,
            message="Password successfully updated. All other active sessions have been revoked for your security.",
            data={"status": "password_changed"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/security/staff/{staff_user_id}/status", response_model=ApiResponse[dict])
def update_staff_status(
    staff_user_id: str,
    payload: StaffStatusUpdateRequest,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN", "BRANCH_ADMIN"])),
    db: Session = Depends(get_db),
):
    try:
        staff = security_privacy_service.update_staff_status(
            db=db,
            staff_user_id=staff_user_id,
            is_active=payload.is_active,
            actor_user=current_user,
            reason=payload.reason,
        )
        action_name = "activated" if payload.is_active else "deactivated"
        return ApiResponse(
            success=True,
            message=f"Staff member '{staff.full_name}' successfully {action_name}",
            data={"staff_id": staff.id, "is_active": staff.is_active},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -------------------------------------------------------------
# 4. MFA Configuration
# -------------------------------------------------------------

@router.get("/security/mfa/status", response_model=ApiResponse[MFAResponse])
def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mfa = security_privacy_service.get_mfa_status(db, current_user.id)
    return ApiResponse(success=True, message="MFA status retrieved", data=MFAResponse(**mfa))


@router.post("/security/mfa/setup", response_model=ApiResponse[MFAResponse])
def setup_mfa(
    payload: MFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mfa = security_privacy_service.setup_mfa(db, current_user, enable=payload.enable, method=payload.method)
    return ApiResponse(
        success=True,
        message=f"Multi-Factor Authentication {'enabled' if payload.enable else 'disabled'} successfully",
        data=MFAResponse(**mfa),
    )


# -------------------------------------------------------------
# 5. Consent Management
# -------------------------------------------------------------

@router.get("/consents/my", response_model=ApiResponse[List[PatientConsentResponse]])
def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        return ApiResponse(success=True, message="No patient profile found", data=[])
    consents = security_privacy_service.list_patient_consents(db, current_user.patient_profile.id)
    resp = [PatientConsentResponse.model_validate(c) for c in consents]
    return ApiResponse(success=True, message="Patient consents retrieved", data=resp)


@router.post("/consents", response_model=ApiResponse[PatientConsentResponse], status_code=status.HTTP_201_CREATED)
def grant_consent(
    payload: PatientConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only registered patients can grant direct personal consent")

    ip = request.client.host if request.client else None
    consent = security_privacy_service.grant_consent(
        db=db,
        patient_id=current_user.patient_profile.id,
        clinic_id=current_user.clinic_id,
        consent_in=payload,
        ip_address=ip,
    )
    return ApiResponse(success=True, message="Consent successfully recorded", data=PatientConsentResponse.model_validate(consent))


@router.post("/consents/{consent_id}/withdraw", response_model=ApiResponse[PatientConsentResponse])
def withdraw_consent(
    consent_id: str,
    payload: PatientConsentWithdraw,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        consent = security_privacy_service.withdraw_consent(
            db=db,
            consent_id=consent_id,
            patient_id=current_user.patient_profile.id,
            reason=payload.reason,
            actor_user=current_user,
        )
        return ApiResponse(success=True, message="Consent successfully revoked and audited", data=PatientConsentResponse.model_validate(consent))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/admin/consents", response_model=ApiResponse[List[PatientConsentResponse]])
def list_admin_consents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    consents = security_privacy_service.list_clinic_consents(
        db, clinic_id=current_user.clinic_id if current_user.role == "ADMIN" else None, skip=skip, limit=limit
    )
    resp = [PatientConsentResponse.model_validate(c) for c in consents]
    return ApiResponse(success=True, message="Clinic consent records retrieved", data=resp)


# -------------------------------------------------------------
# 6. Privacy Workflows (DSAR: Data Export & Deletion)
# -------------------------------------------------------------

@router.get("/privacy/requests/my", response_model=ApiResponse[List[PrivacyRequestResponse]])
def get_my_privacy_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        return ApiResponse(success=True, message="No patient profile found", data=[])

    requests = security_privacy_service.list_patient_privacy_requests(db, current_user.patient_profile.id)
    resp = []
    for r in requests:
        payload_dict = json.loads(r.export_payload) if r.export_payload else None
        resp.append(
            PrivacyRequestResponse(
                id=r.id,
                patient_id=r.patient_id,
                request_type=r.request_type,
                status=r.status,
                reason=r.reason,
                retention_note=r.retention_note,
                export_payload=payload_dict,
                requested_at=r.requested_at,
                processed_at=r.processed_at,
                created_at=r.created_at,
            )
        )
    return ApiResponse(success=True, message="Privacy requests retrieved", data=resp)


@router.post("/privacy/export-request", response_model=ApiResponse[PrivacyRequestResponse], status_code=status.HTTP_201_CREATED)
def request_data_export(
    payload: PrivacyRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient profile required for export request")

    payload.request_type = "DATA_EXPORT"
    req_obj = security_privacy_service.create_privacy_request(db, current_user.patient_profile.id, payload)
    payload_dict = json.loads(req_obj.export_payload) if req_obj.export_payload else None
    resp = PrivacyRequestResponse(
        id=req_obj.id,
        patient_id=req_obj.patient_id,
        request_type=req_obj.request_type,
        status=req_obj.status,
        reason=req_obj.reason,
        retention_note=req_obj.retention_note,
        export_payload=payload_dict,
        requested_at=req_obj.requested_at,
        processed_at=req_obj.processed_at,
        created_at=req_obj.created_at,
    )
    return ApiResponse(success=True, message="Data export request processed successfully", data=resp)


@router.post("/privacy/deletion-request", response_model=ApiResponse[PrivacyRequestResponse], status_code=status.HTTP_201_CREATED)
def request_data_deletion(
    payload: PrivacyRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient profile required for deletion request")

    payload.request_type = "DATA_DELETION"
    req_obj = security_privacy_service.create_privacy_request(db, current_user.patient_profile.id, payload)
    resp = PrivacyRequestResponse(
        id=req_obj.id,
        patient_id=req_obj.patient_id,
        request_type=req_obj.request_type,
        status=req_obj.status,
        reason=req_obj.reason,
        retention_note=req_obj.retention_note,
        requested_at=req_obj.requested_at,
        processed_at=req_obj.processed_at,
        created_at=req_obj.created_at,
    )
    return ApiResponse(
        success=True,
        message="Data deletion request submitted. Regulated clinical data is subject to statutory retention review.",
        data=resp,
    )


@router.get("/admin/privacy/requests", response_model=ApiResponse[List[PrivacyRequestResponse]])
def list_admin_privacy_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    requests = security_privacy_service.list_all_privacy_requests(db, skip=skip, limit=limit)
    resp = []
    for r in requests:
        payload_dict = json.loads(r.export_payload) if r.export_payload else None
        resp.append(
            PrivacyRequestResponse(
                id=r.id,
                patient_id=r.patient_id,
                request_type=r.request_type,
                status=r.status,
                reason=r.reason,
                retention_note=r.retention_note,
                export_payload=payload_dict,
                requested_at=r.requested_at,
                processed_at=r.processed_at,
                created_at=r.created_at,
            )
        )
    return ApiResponse(success=True, message="DSAR privacy requests retrieved", data=resp)


@router.post("/admin/privacy/requests/{request_id}/process", response_model=ApiResponse[PrivacyRequestResponse])
def process_admin_privacy_request(
    request_id: str,
    payload: PrivacyRequestProcess,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    try:
        req_obj = security_privacy_service.process_privacy_request(db, request_id, payload, current_user)
        payload_dict = json.loads(req_obj.export_payload) if req_obj.export_payload else None
        resp = PrivacyRequestResponse(
            id=req_obj.id,
            patient_id=req_obj.patient_id,
            request_type=req_obj.request_type,
            status=req_obj.status,
            reason=req_obj.reason,
            retention_note=req_obj.retention_note,
            export_payload=payload_dict,
            requested_at=req_obj.requested_at,
            processed_at=req_obj.processed_at,
            created_at=req_obj.created_at,
        )
        return ApiResponse(success=True, message=f"Privacy request marked as {req_obj.status}", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
