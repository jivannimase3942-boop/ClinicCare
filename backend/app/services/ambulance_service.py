from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.ambulance import Ambulance, AmbulanceRequest
from app.models.user import Patient, User
from app.schemas.ambulance import (
    AmbulanceResponse,
    AmbulanceCreate,
    AmbulanceStatusUpdate,
    AmbulanceRequestCreate,
    AmbulanceRequestResponse,
    AmbulanceRequestStatusUpdate,
)


class AmbulanceService:
    @staticmethod
    def get_all_ambulances(
        db: Session,
        status: Optional[str] = None,
        active_only: bool = True
    ) -> List[AmbulanceResponse]:
        query = db.query(Ambulance)
        if active_only:
            query = query.filter(Ambulance.is_active == True)
        if status:
            query = query.filter(Ambulance.status == status)
        ambulances = query.order_by(Ambulance.vehicle_number.asc()).all()
        return [AmbulanceResponse.model_validate(a) for a in ambulances]

    @staticmethod
    def create_ambulance(db: Session, data: AmbulanceCreate) -> AmbulanceResponse:
        amb = Ambulance(
            vehicle_number=data.vehicle_number,
            model=data.model,
            ambulance_type=data.ambulance_type or "Basic Life Support (BLS)",
            base_station=data.base_station or "ClinicCare Main Campus",
            current_location=data.current_location or "Main Base, Bay 1",
            driver_name=data.driver_name,
            driver_phone=data.driver_phone,
            paramedic_name=data.paramedic_name,
            status="available",
            is_active=True,
        )
        db.add(amb)
        db.commit()
        db.refresh(amb)
        return AmbulanceResponse.model_validate(amb)

    @staticmethod
    def update_ambulance_status(
        db: Session,
        ambulance_id: str,
        data: AmbulanceStatusUpdate
    ) -> AmbulanceResponse:
        amb = db.query(Ambulance).filter(Ambulance.id == ambulance_id).first()
        if not amb:
            raise ValueError("Ambulance not found")
        amb.status = data.status
        if data.current_location:
            amb.current_location = data.current_location
        db.commit()
        db.refresh(amb)
        return AmbulanceResponse.model_validate(amb)

    @staticmethod
    def _format_request(req: AmbulanceRequest) -> AmbulanceRequestResponse:
        pat_name = req.patient.user.full_name if req.patient and req.patient.user else req.requester_name
        veh_num = req.ambulance.vehicle_number if req.ambulance else None
        amb_mod = req.ambulance.model if req.ambulance else None
        drv_name = req.ambulance.driver_name if req.ambulance else None
        drv_phone = req.ambulance.driver_phone if req.ambulance else None

        return AmbulanceRequestResponse(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=pat_name,
            ambulance_id=req.ambulance_id,
            ambulance_vehicle_number=veh_num,
            ambulance_model=amb_mod,
            driver_name=drv_name,
            driver_phone=drv_phone,
            requester_name=req.requester_name,
            requester_phone=req.requester_phone,
            pickup_address=req.pickup_address,
            destination_facility=req.destination_facility,
            emergency_priority=req.emergency_priority,
            status=req.status,
            notes=req.notes,
            is_simulated=req.is_simulated,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )

    @staticmethod
    def request_ambulance(
        db: Session,
        data: AmbulanceRequestCreate,
        patient_id: Optional[str] = None
    ) -> AmbulanceRequestResponse:
        available_amb = None
        if data.emergency_priority in ["critical", "high"]:
            available_amb = db.query(Ambulance).filter(
                Ambulance.status == "available",
                Ambulance.is_active == True
            ).first()

        req_status = "assigned" if available_amb else "requested"
        if available_amb:
            available_amb.status = "busy"
            available_amb.current_location = f"En route to {data.pickup_address[:30]}"

        req = AmbulanceRequest(
            patient_id=patient_id or data.patient_id,
            ambulance_id=available_amb.id if available_amb else None,
            requester_name=data.requester_name,
            requester_phone=data.requester_phone,
            pickup_address=data.pickup_address,
            destination_facility=data.destination_facility or "ClinicCare Multispeciality Hospital",
            emergency_priority=data.emergency_priority or "high",
            status=req_status,
            notes=data.notes,
            is_simulated=True,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return AmbulanceService._format_request(req)

    @staticmethod
    def get_ambulance_requests(
        db: Session,
        status: Optional[str] = None,
        patient_id: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[AmbulanceRequestResponse]:
        query = db.query(AmbulanceRequest)
        if patient_id:
            query = query.filter(AmbulanceRequest.patient_id == patient_id)
        if status:
            query = query.filter(AmbulanceRequest.status == status)
        if priority:
            query = query.filter(AmbulanceRequest.emergency_priority == priority)
        requests = query.order_by(AmbulanceRequest.created_at.desc()).all()
        return [AmbulanceService._format_request(r) for r in requests]

    @staticmethod
    def update_request_status(
        db: Session,
        request_id: str,
        data: AmbulanceRequestStatusUpdate
    ) -> AmbulanceRequestResponse:
        req = db.query(AmbulanceRequest).filter(AmbulanceRequest.id == request_id).first()
        if not req:
            raise ValueError("Ambulance request not found")
        req.status = data.status
        if data.notes:
            req.notes = (req.notes or "") + f" [{data.notes}]"
        if data.ambulance_id:
            req.ambulance_id = data.ambulance_id

        if data.status in ["completed", "cancelled"] and req.ambulance:
            req.ambulance.status = "available"
            req.ambulance.current_location = req.ambulance.base_station

        db.commit()
        db.refresh(req)
        return AmbulanceService._format_request(req)

    @staticmethod
    def assign_ambulance_to_request(
        db: Session,
        request_id: str,
        ambulance_id: str,
        notes: Optional[str] = None
    ) -> AmbulanceRequestResponse:
        req = db.query(AmbulanceRequest).filter(AmbulanceRequest.id == request_id).first()
        if not req:
            raise ValueError("Ambulance request not found")
        amb = db.query(Ambulance).filter(Ambulance.id == ambulance_id).first()
        if not amb:
            raise ValueError("Ambulance not found")

        req.ambulance_id = amb.id
        req.status = "assigned"
        amb.status = "busy"
        amb.current_location = f"Dispatched to {req.pickup_address[:30]}"
        if notes:
            req.notes = (req.notes or "") + f" [{notes}]"

        db.commit()
        db.refresh(req)
        return AmbulanceService._format_request(req)


ambulance_service = AmbulanceService()

