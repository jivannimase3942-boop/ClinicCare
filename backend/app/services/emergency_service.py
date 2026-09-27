from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.escalation import Escalation
from app.models.ambulance import Ambulance, AmbulanceRequest
from app.models.user import Patient, User
from app.schemas.emergency import EmergencyRequestCreate, EmergencyRequestResponse, EmergencyStatsResponse


class EmergencyService:
    @staticmethod
    def get_emergency_stats(db: Session) -> EmergencyStatsResponse:
        total = db.query(func.count(Escalation.id)).filter(
            Escalation.reason.in_(["emergency", "medical_question"])
        ).scalar() or 0

        active_crit = db.query(func.count(Escalation.id)).filter(
            Escalation.priority.in_(["emergency", "high"]),
            Escalation.status.in_(["open", "assigned", "in_progress"])
        ).scalar() or 0

        dispatched = db.query(func.count(AmbulanceRequest.id)).filter(
            AmbulanceRequest.status.in_(["assigned", "en_route"])
        ).scalar() or 0

        today = date.today()
        resolved_today = db.query(func.count(Escalation.id)).filter(
            Escalation.status == "resolved",
            Escalation.updated_at >= datetime.combine(today, datetime.min.time())
        ).scalar() or 0

        return EmergencyStatsResponse(
            total_emergencies=total,
            critical_active=active_crit,
            dispatched_ambulances=dispatched,
            resolved_today=resolved_today,
            average_response_minutes=4.5,
        )

    @staticmethod
    def create_emergency_request(
        db: Session,
        data: EmergencyRequestCreate
    ) -> EmergencyRequestResponse:
        # Create escalation
        esc = Escalation(
            patient_id=data.patient_id or db.query(Patient.id).first()[0],
            reason="emergency",
            priority="emergency" if data.priority == "critical" else (data.priority or "high"),
            status="open",
            resolution_notes=f"Emergency: {data.emergency_type} at {data.location}. Caller: {data.caller_name} ({data.caller_phone}). Notes: {data.notes or 'None'}",
        )
        db.add(esc)
        db.commit()
        db.refresh(esc)

        amb_req_id = None
        amb_veh = None
        if data.requires_ambulance:
            avail_amb = db.query(Ambulance).filter(Ambulance.status == "available", Ambulance.is_active == True).first()
            if avail_amb:
                avail_amb.status = "busy"
                avail_amb.current_location = f"En route to {data.location[:30]}"
                amb_veh = avail_amb.vehicle_number

            amb_req = AmbulanceRequest(
                patient_id=data.patient_id,
                ambulance_id=avail_amb.id if avail_amb else None,
                requester_name=data.caller_name,
                requester_phone=data.caller_phone,
                pickup_address=data.location,
                destination_facility="ClinicCare Multispeciality Hospital",
                emergency_priority="critical",
                status="assigned" if avail_amb else "requested",
                notes=f"Auto-dispatched via Emergency Coordination: {data.emergency_type}",
                is_simulated=True,
            )
            db.add(amb_req)
            db.commit()
            db.refresh(amb_req)
            amb_req_id = amb_req.id

        return EmergencyRequestResponse(
            id=esc.id,
            patient_id=esc.patient_id,
            patient_name=esc.patient.user.full_name if esc.patient and esc.patient.user else data.caller_name,
            caller_name=data.caller_name,
            caller_phone=data.caller_phone,
            location=data.location,
            emergency_type=data.emergency_type,
            priority=esc.priority,
            status=esc.status,
            ambulance_id=amb_req_id,
            ambulance_vehicle_number=amb_veh,
            assigned_staff_id=esc.assigned_to_user_id,
            assigned_staff_name=esc.assigned_staff.full_name if esc.assigned_staff else None,
            resolution_notes=esc.resolution_notes,
            created_at=esc.created_at,
            updated_at=esc.updated_at,
        )


emergency_service = EmergencyService()
