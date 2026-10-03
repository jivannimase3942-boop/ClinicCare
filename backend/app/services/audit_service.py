import json
from typing import Optional, Any, List, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        user: Optional[User] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        clinic_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[AuditLog]:
        try:
            resolved_uid = user.id if user else user_id
            resolved_email = user.email if user else user_email
            resolved_role = user.role if user else user_role
            resolved_clinic = (user.clinic_id if user and user.clinic_id else clinic_id)

            details_str = None
            if details is not None:
                if isinstance(details, (dict, list)):
                    try:
                        details_str = json.dumps(details)
                    except Exception:
                        details_str = str(details)
                else:
                    details_str = str(details)

            audit_entry = AuditLog(
                clinic_id=resolved_clinic,
                user_id=resolved_uid,
                user_email=resolved_email,
                user_role=resolved_role,
                action=action.upper(),
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                details=details_str,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            return audit_entry
        except Exception as e:
            print(f"[AuditService] Warning: Failed to record audit log: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None

    @staticmethod
    def get_logs(
        db: Session,
        clinic_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        q = db.query(AuditLog)
        if clinic_id:
            q = q.filter(AuditLog.clinic_id == clinic_id)
        if action:
            q = q.filter(AuditLog.action == action.upper())
        if entity_type:
            q = q.filter(AuditLog.entity_type == entity_type)
        return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


audit_service = AuditService()
