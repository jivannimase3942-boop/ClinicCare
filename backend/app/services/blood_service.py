from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.blood import BloodBank, BloodInventory, BloodRequest
from app.schemas.blood import (
    BloodBankResponse,
    BloodGroupSearchResult,
    BloodInventoryItem,
    BloodInventoryUpdate,
    BloodRequestCreate,
    BloodRequestResponse,
    BloodRequestStatusUpdate,
)


class BloodService:
    @staticmethod
    def get_all_blood_banks(
        db: Session,
        city: Optional[str] = None
    ) -> List[BloodBankResponse]:
        query = db.query(BloodBank)
        if city:
            query = query.filter(BloodBank.city.ilike(f"%{city}%"))
        banks = query.order_by(BloodBank.name.asc()).all()
        result = []
        for b in banks:
            inv_items = [BloodInventoryItem.model_validate(inv) for inv in b.inventory]
            result.append(
                BloodBankResponse(
                    id=b.id,
                    name=b.name,
                    city=b.city,
                    address=b.address,
                    phone=b.phone,
                    email=b.email,
                    operating_hours=b.operating_hours,
                    is_verified=b.is_verified,
                    inventory=inv_items,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                )
            )
        return result

    @staticmethod
    def search_blood_group(
        db: Session,
        blood_group: str,
        city: Optional[str] = None
    ) -> List[BloodGroupSearchResult]:
        query = db.query(BloodInventory).join(BloodBank, BloodInventory.blood_bank_id == BloodBank.id)
        if blood_group and blood_group.strip():
            bg_clean = blood_group.strip().upper()
            query = query.filter(BloodInventory.blood_group == bg_clean)
        if city and city.strip():
            query = query.filter(BloodBank.city.ilike(f"%{city.strip()}%"))

        records = query.order_by(BloodInventory.units_available.desc()).all()
        results = []
        for r in records:
            results.append(
                BloodGroupSearchResult(
                    blood_bank_id=r.blood_bank.id,
                    blood_bank_name=r.blood_bank.name,
                    city=r.blood_bank.city,
                    address=r.blood_bank.address,
                    phone=r.blood_bank.phone,
                    blood_group=r.blood_group,
                    units_available=r.units_available,
                    status=r.status,
                    last_updated=r.last_updated,
                    operating_hours=r.blood_bank.operating_hours,
                )
            )
        return results

    @staticmethod
    def update_inventory_units(
        db: Session,
        inventory_id: str,
        data: BloodInventoryUpdate
    ) -> BloodInventoryItem:
        item = db.query(BloodInventory).filter(BloodInventory.id == inventory_id).first()
        if not item:
            raise ValueError("Blood inventory record not found")
        item.units_available = data.units_available
        if data.status:
            item.status = data.status
        else:
            if item.units_available == 0:
                item.status = "critical_need"
            elif item.units_available < 5:
                item.status = "low_stock"
            else:
                item.status = "available"
        db.commit()
        db.refresh(item)
        return BloodInventoryItem.model_validate(item)

    @staticmethod
    def create_blood_request(
        db: Session,
        data: BloodRequestCreate,
        patient_id: Optional[str] = None
    ) -> BloodRequestResponse:
        req = BloodRequest(
            patient_id=patient_id or data.patient_id,
            patient_name=data.patient_name,
            blood_group=data.blood_group.strip().upper(),
            units_required=data.units_required,
            hospital_clinic_name=data.hospital_clinic_name,
            location=data.location,
            contact_phone=data.contact_phone,
            urgency=data.urgency or "urgent",
            additional_info=data.additional_info,
            status="submitted",
            is_simulated=True,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return BloodRequestResponse.model_validate(req)

    @staticmethod
    def get_blood_requests(
        db: Session,
        status: Optional[str] = None,
        blood_group: Optional[str] = None,
        patient_id: Optional[str] = None,
        urgency: Optional[str] = None,
    ) -> List[BloodRequestResponse]:
        query = db.query(BloodRequest)
        if patient_id:
            query = query.filter(BloodRequest.patient_id == patient_id)
        if status:
            query = query.filter(BloodRequest.status == status)
        if blood_group:
            query = query.filter(BloodRequest.blood_group == blood_group.strip().upper())
        if urgency:
            query = query.filter(BloodRequest.urgency == urgency)
        requests = query.order_by(BloodRequest.created_at.desc()).all()
        return [BloodRequestResponse.model_validate(r) for r in requests]

    @staticmethod
    def update_blood_request_status(
        db: Session,
        request_id: str,
        data: BloodRequestStatusUpdate
    ) -> BloodRequestResponse:
        req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
        if not req:
            raise ValueError("Blood request not found")
        req.status = data.status
        if data.admin_notes:
            req.admin_notes = data.admin_notes
        if data.matched_blood_bank_id:
            req.matched_blood_bank_id = data.matched_blood_bank_id
        if data.matched_bank_name:
            req.matched_bank_name = data.matched_bank_name
        db.commit()
        db.refresh(req)
        return BloodRequestResponse.model_validate(req)

    @staticmethod
    def match_blood_bank(
        db: Session,
        request_id: str,
        blood_bank_id: str,
        notes: Optional[str] = None
    ) -> BloodRequestResponse:
        req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
        if not req:
            raise ValueError("Blood request not found")
        bank = db.query(BloodBank).filter(BloodBank.id == blood_bank_id).first()
        if not bank:
            raise ValueError("Blood bank not found")

        req.matched_blood_bank_id = bank.id
        req.matched_bank_name = f"{bank.name} ({bank.city})"
        req.status = "match_found"
        if notes:
            req.admin_notes = notes
        db.commit()
        db.refresh(req)
        return BloodRequestResponse.model_validate(req)


blood_service = BloodService()
