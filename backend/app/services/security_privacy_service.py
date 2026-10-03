import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.security_privacy import (
    UserSession,
    SecurityEvent,
    PatientConsent,
    PrivacyRequest,
    MFAConfig,
)
from app.models.user import User, Patient
from app.models.clinical import ConsultationRecord, VitalSign
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.billing import Invoice
from app.core.security import verify_password, get_password_hash
from app.services.audit_service import audit_service
from app.schemas.security_privacy import (
    PatientConsentCreate,
    PrivacyRequestCreate,
    PrivacyRequestProcess,
)


class SecurityPrivacyService:
    # -------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------
    @staticmethod
    def create_session(
        db: Session,
        user: User,
        token_jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> UserSession:
        session = UserSession(
            user_id=user.id,
            token_jti=token_jti,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            device_info=device_info,
            is_active=True,
            last_activity_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_active_sessions(db: Session, user_id: str) -> List[UserSession]:
        now = datetime.now(timezone.utc)
        return (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > now,
            )
            .order_by(UserSession.last_activity_at.desc())
            .all()
        )

    @staticmethod
    def revoke_session(db: Session, user_id: str, token_jti: str) -> bool:
        session = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.token_jti == token_jti,
                UserSession.is_active == True,
            )
            .first()
        )
        if session:
            session.is_active = False
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False

    @staticmethod
    def revoke_all_sessions(db: Session, user_id: str, except_jti: Optional[str] = None) -> int:
        now = datetime.now(timezone.utc)
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )
        if except_jti:
            query = query.filter(UserSession.token_jti != except_jti)

        sessions = query.all()
        count = len(sessions)
        for s in sessions:
            s.is_active = False
            s.revoked_at = now
        db.commit()
        return count

    @staticmethod
    def is_session_active(db: Session, token_jti: str) -> bool:
        session = db.query(UserSession).filter(UserSession.token_jti == token_jti).first()
        if not session:
            # If session is untracked (legacy/test token), treat as valid
            return True
        if not session.is_active:
            return False
        if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            session.is_active = False
            db.commit()
            return False
        return True

    # -------------------------------------------------------------
    # Security Events
    # -------------------------------------------------------------
    @staticmethod
    def record_security_event(
        db: Session,
        event_type: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        clinic_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        severity: str = "INFO",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> SecurityEvent:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
        event = SecurityEvent(
            user_id=user_id,
            user_email=user_email,
            clinic_id=clinic_id,
            branch_id=branch_id,
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            details=details_str,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Mirror into central audit log for Unified Compliance
        audit_service.log_action(
            db=db,
            action=event_type,
            user_id=user_id,
            user_email=user_email,
            clinic_id=clinic_id,
            entity_type="SECURITY_EVENT",
            entity_id=event.id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return event

    @staticmethod
    def list_security_events(
        db: Session,
        clinic_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SecurityEvent]:
        q = db.query(SecurityEvent)
        if clinic_id:
            q = q.filter(SecurityEvent.clinic_id == clinic_id)
        if user_id:
            q = q.filter(SecurityEvent.user_id == user_id)
        return q.order_by(SecurityEvent.created_at.desc()).offset(offset).limit(limit).all()

    # -------------------------------------------------------------
    # Password & Staff Operations
    # -------------------------------------------------------------
    @staticmethod
    def change_password(
        db: Session,
        user: User,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        if not verify_password(old_password, user.password_hash):
            SecurityPrivacyService.record_security_event(
                db=db,
                event_type="PASSWORD_CHANGE_FAILED",
                user_id=user.id,
                user_email=user.email,
                clinic_id=user.clinic_id,
                severity="WARNING",
                ip_address=ip_address,
                user_agent=user_agent,
                details="Invalid current password supplied during change request",
            )
            raise ValueError("Current password is incorrect")

        user.password_hash = get_password_hash(new_password)
        db.commit()

        # Log out all other sessions on password change
        SecurityPrivacyService.revoke_all_sessions(db, user.id)

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="PASSWORD_CHANGE",
            user_id=user.id,
            user_email=user.email,
            clinic_id=user.clinic_id,
            severity="INFO",
            ip_address=ip_address,
            user_agent=user_agent,
            details="Password successfully updated; all existing sessions revoked",
        )
        return True

    @staticmethod
    def update_staff_status(
        db: Session,
        staff_user_id: str,
        is_active: bool,
        actor_user: User,
        reason: Optional[str] = None,
    ) -> User:
        staff = db.query(User).filter(User.id == staff_user_id).first()
        if not staff:
            raise ValueError("Staff member not found")

        staff.is_active = is_active
        if not is_active:
            # Immediately revoke all active sessions if deactivated
            SecurityPrivacyService.revoke_all_sessions(db, staff.id)

        db.commit()

        event_type = "STAFF_ACTIVATION" if is_active else "STAFF_DEACTIVATION"
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type=event_type,
            user_id=staff.id,
            user_email=staff.email,
            clinic_id=staff.clinic_id,
            severity="WARNING" if not is_active else "INFO",
            details={
                "actor_id": actor_user.id,
                "actor_email": actor_user.email,
                "action": "ACTIVATED" if is_active else "DEACTIVATED",
                "reason": reason or "Administrative change",
            },
        )
        return staff

    # -------------------------------------------------------------
    # MFA Management
    # -------------------------------------------------------------
    @staticmethod
    def get_mfa_status(db: Session, user_id: str) -> Dict[str, Any]:
        config = db.query(MFAConfig).filter(MFAConfig.user_id == user_id).first()
        if not config:
            return {"is_enabled": False, "method": "EMAIL_OTP", "configured": True}
        return {
            "is_enabled": config.is_enabled,
            "method": config.method,
            "configured": True,
            "last_verified_at": config.last_verified_at,
        }

    @staticmethod
    def setup_mfa(db: Session, user: User, enable: bool, method: str = "EMAIL_OTP") -> Dict[str, Any]:
        config = db.query(MFAConfig).filter(MFAConfig.user_id == user.id).first()
        if not config:
            config = MFAConfig(user_id=user.id, is_enabled=enable, method=method)
            db.add(config)
        else:
            config.is_enabled = enable
            config.method = method
            config.updated_at = datetime.now(timezone.utc)
        db.commit()

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="MFA_STATUS_CHANGED",
            user_id=user.id,
            user_email=user.email,
            clinic_id=user.clinic_id,
            severity="INFO",
            details=f"MFA set to is_enabled={enable}, method={method}",
        )
        return {"is_enabled": config.is_enabled, "method": config.method, "configured": True}

    # -------------------------------------------------------------
    # Patient Consent Management
    # -------------------------------------------------------------
    @staticmethod
    def grant_consent(
        db: Session,
        patient_id: str,
        clinic_id: Optional[str],
        consent_in: PatientConsentCreate,
        ip_address: Optional[str] = None,
    ) -> PatientConsent:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        consent = PatientConsent(
            patient_id=patient.id,
            clinic_id=clinic_id,
            consent_type=consent_in.consent_type.upper(),
            purpose=consent_in.purpose,
            status="GRANTED",
            source=consent_in.source,
            ip_address=ip_address,
            granted_at=datetime.now(timezone.utc),
            expires_at=consent_in.expires_at,
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="CONSENT_GRANTED",
            user_id=patient.user_id,
            clinic_id=clinic_id,
            severity="INFO",
            ip_address=ip_address,
            details={
                "consent_id": consent.id,
                "type": consent.consent_type,
                "purpose": consent.purpose,
                "source": consent.source,
            },
        )
        return consent

    @staticmethod
    def withdraw_consent(
        db: Session,
        consent_id: str,
        patient_id: str,
        reason: Optional[str] = None,
        actor_user: Optional[User] = None,
    ) -> PatientConsent:
        consent = (
            db.query(PatientConsent)
            .filter(PatientConsent.id == consent_id, PatientConsent.patient_id == patient_id)
            .first()
        )
        if not consent:
            raise ValueError("Consent record not found")

        consent.status = "REVOKED"
        consent.revoked_at = datetime.now(timezone.utc)
        consent.revoked_reason = reason
        db.commit()
        db.refresh(consent)

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="CONSENT_REVOKED",
            user_id=actor_user.id if actor_user else None,
            clinic_id=consent.clinic_id,
            severity="WARNING",
            details={
                "consent_id": consent.id,
                "type": consent.consent_type,
                "reason": reason or "Withdrawn by patient",
            },
        )
        return consent

    @staticmethod
    def list_patient_consents(db: Session, patient_id: str) -> List[PatientConsent]:
        return (
            db.query(PatientConsent)
            .filter(PatientConsent.patient_id == patient_id)
            .order_by(PatientConsent.created_at.desc())
            .all()
        )

    @staticmethod
    def list_clinic_consents(db: Session, clinic_id: Optional[str], skip: int = 0, limit: int = 50) -> List[PatientConsent]:
        q = db.query(PatientConsent)
        if clinic_id:
            q = q.filter(PatientConsent.clinic_id == clinic_id)
        return q.order_by(PatientConsent.created_at.desc()).offset(skip).limit(limit).all()

    # -------------------------------------------------------------
    # Privacy Workflows (DSAR: Data Export & Deletion Request)
    # -------------------------------------------------------------
    @staticmethod
    def create_privacy_request(
        db: Session,
        patient_id: str,
        req_in: PrivacyRequestCreate,
    ) -> PrivacyRequest:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient profile not found")

        req_type = req_in.request_type.upper().strip()
        if req_type not in ["DATA_EXPORT", "DATA_DELETION"]:
            raise ValueError("Request type must be DATA_EXPORT or DATA_DELETION")

        retention_note = None
        if req_type == "DATA_DELETION":
            retention_note = (
                "Statutory Healthcare Retention Notice: In accordance with Indian Medical Council Regulations, "
                "NABH Standards, and applicable healthcare compliance rules, core clinical health records must be "
                "retained for a mandatory minimum statutory period (3-5 years). Account credentials and marketing communications "
                "will be deactivated immediately upon administrative review, with clinical records safely archived under restricted custody."
            )

        export_data = None
        status = "PENDING"
        if req_type == "DATA_EXPORT":
            # Instantly compile export payload
            status = "COMPLETED"
            export_data = SecurityPrivacyService.compile_patient_export(db, patient)

        req_obj = PrivacyRequest(
            patient_id=patient.id,
            request_type=req_type,
            status=status,
            reason=req_in.reason,
            retention_note=retention_note,
            export_payload=json.dumps(export_data) if export_data else None,
            requested_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc) if status == "COMPLETED" else None,
        )
        db.add(req_obj)
        db.commit()
        db.refresh(req_obj)

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type=f"PRIVACY_{req_type}_REQUESTED",
            user_id=patient.user_id,
            severity="INFO" if req_type == "DATA_EXPORT" else "WARNING",
            details={"request_id": req_obj.id, "type": req_type, "status": req_obj.status},
        )
        return req_obj

    @staticmethod
    def compile_patient_export(db: Session, patient: Patient) -> Dict[str, Any]:
        """Compiles clean, authorized patient data for export."""
        user = patient.user
        appointments = db.query(Appointment).filter(Appointment.patient_id == patient.id).all()
        consultations = db.query(ConsultationRecord).filter(ConsultationRecord.patient_id == patient.id).all()
        vitals = db.query(VitalSign).filter(VitalSign.patient_id == patient.id).all()
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient.id).all()
        invoices = db.query(Invoice).filter(Invoice.patient_id == patient.id).all()
        consents = db.query(PatientConsent).filter(PatientConsent.patient_id == patient.id).all()

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "patient": {
                "id": patient.id,
                "full_name": user.full_name if user else None,
                "email": user.email if user else None,
                "phone": user.phone if user else None,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
                "address": patient.address,
                "emergency_contact": patient.emergency_contact,
            },
            "appointments_count": len(appointments),
            "consultations_count": len(consultations),
            "vitals_count": len(vitals),
            "prescriptions_count": len(prescriptions),
            "invoices_count": len(invoices),
            "consents": [
                {
                    "type": c.consent_type,
                    "purpose": c.purpose,
                    "status": c.status,
                    "granted_at": c.granted_at.isoformat(),
                }
                for c in consents
            ],
        }

    @staticmethod
    def list_patient_privacy_requests(db: Session, patient_id: str) -> List[PrivacyRequest]:
        return (
            db.query(PrivacyRequest)
            .filter(PrivacyRequest.patient_id == patient_id)
            .order_by(PrivacyRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def list_all_privacy_requests(db: Session, skip: int = 0, limit: int = 50) -> List[PrivacyRequest]:
        return db.query(PrivacyRequest).order_by(PrivacyRequest.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def process_privacy_request(
        db: Session,
        request_id: str,
        process_in: PrivacyRequestProcess,
        processor_user: User,
    ) -> PrivacyRequest:
        req_obj = db.query(PrivacyRequest).filter(PrivacyRequest.id == request_id).first()
        if not req_obj:
            raise ValueError("Privacy request not found")

        req_obj.status = process_in.status.upper()
        if process_in.retention_note:
            req_obj.retention_note = process_in.retention_note
        req_obj.processed_at = datetime.now(timezone.utc)
        req_obj.processed_by_user_id = processor_user.id
        db.commit()
        db.refresh(req_obj)

        SecurityPrivacyService.record_security_event(
            db=db,
            event_type=f"PRIVACY_REQUEST_{req_obj.status}",
            user_id=processor_user.id,
            severity="INFO",
            details={
                "request_id": req_obj.id,
                "patient_id": req_obj.patient_id,
                "status": req_obj.status,
                "processed_by": processor_user.email,
            },
        )
        return req_obj


security_privacy_service = SecurityPrivacyService()
