from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.emergency import (
    EmergencyRequestCreate,
    EmergencyRequestResponse,
    EmergencyStatsResponse,
)
from app.services.emergency_service import emergency_service
from app.services.escalation_service import escalation_service
from app.api.dependencies import require_roles, get_optional_patient
from app.models.user import Patient

router = APIRouter(prefix="/emergencies", tags=["Emergency Coordination"])


@router.get("/stats", response_model=ApiResponse[EmergencyStatsResponse])
def get_emergency_stats(db: Session = Depends(get_db)):
    stats = emergency_service.get_emergency_stats(db)
    return ApiResponse(success=True, data=stats)


@router.post("", response_model=ApiResponse[EmergencyRequestResponse], status_code=status.HTTP_201_CREATED)
def create_emergency_request(
    data: EmergencyRequestCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        if current_patient and not data.patient_id:
            data.patient_id = current_patient.id
        req = emergency_service.create_emergency_request(db, data)
        return ApiResponse(success=True, message="Emergency request created and dispatched", data=req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=ApiResponse[List[EmergencyRequestResponse]])
def list_emergencies(db: Session = Depends(get_db)):
    from app.models.escalation import Escalation
    escs = db.query(Escalation).filter(Escalation.reason.in_(["emergency", "medical_question"])).order_by(Escalation.created_at.desc()).all()
    results = []
    for e in escs:
        pat_name = e.patient.user.full_name if e.patient and e.patient.user else "Emergency Caller"
        pat_phone = e.patient.user.phone if e.patient and e.patient.user else "Emergency Contact"
        results.append(
            EmergencyRequestResponse(
                id=e.id,
                patient_id=e.patient_id,
                patient_name=pat_name,
                caller_name=pat_name,
                caller_phone=pat_phone,
                location=e.resolution_notes or "ClinicCare Emergency OPD",
                emergency_type="Clinical Emergency" if e.reason == "emergency" else "Urgent Medical Inquiry",
                priority=e.priority,
                status=e.status,
                assigned_staff_id=e.assigned_to_user_id,
                assigned_staff_name=e.assigned_staff.full_name if e.assigned_staff else None,
                resolution_notes=e.resolution_notes,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
        )
    return ApiResponse(success=True, data=results)
