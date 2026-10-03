from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.models.prescription import Medicine, Prescription, PrescriptionItem
from app.models.user import Patient, Doctor, User
from app.models.clinic import Clinic
from app.schemas.prescription import (
    MedicineCreate,
    MedicineResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    PrescriptionItemResponse,
)
from app.services.audit_service import audit_service


class PrescriptionService:
    @staticmethod
    def generate_prescription_number(db: Session) -> str:
        now = datetime.now(timezone.utc)
        prefix = f"RX-{now.strftime('%Y%m')}-"
        count = db.query(Prescription).filter(Prescription.prescription_number.like(f"{prefix}%")).count()
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def _format_prescription(p: Prescription) -> PrescriptionResponse:
        items_resp = [PrescriptionItemResponse.model_validate(it) for it in p.items]
        patient_name = p.patient.user.full_name if (p.patient and p.patient.user) else None
        patient_phone = p.patient.user.phone if (p.patient and p.patient.user) else None
        patient_gender = p.patient.gender if p.patient else None

        doctor_name = p.doctor.user.full_name if (p.doctor and p.doctor.user) else None
        doctor_spec = p.doctor.specialization if p.doctor else None
        doctor_qual = p.doctor.qualification if p.doctor else None

        clinic_name = p.clinic.name if p.clinic else None
        clinic_addr = p.clinic.address if p.clinic else None
        clinic_phone = p.clinic.phone if p.clinic else None

        return PrescriptionResponse(
            id=p.id,
            prescription_number=p.prescription_number,
            clinic_id=p.clinic_id,
            clinic_name=clinic_name,
            clinic_address=clinic_addr,
            clinic_phone=clinic_phone,
            patient_id=p.patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_gender=patient_gender,
            doctor_id=p.doctor_id,
            doctor_name=doctor_name,
            doctor_specialization=doctor_spec,
            doctor_qualification=doctor_qual,
            appointment_id=p.appointment_id,
            consultation_id=p.consultation_id,
            status=p.status,
            diagnosis_summary=p.diagnosis_summary,
            general_advice=p.general_advice,
            diet_lifestyle_notes=p.diet_lifestyle_notes,
            follow_up_date=p.follow_up_date,
            is_finalized=p.is_finalized,
            finalized_at=p.finalized_at,
            items=items_resp,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def list_medicines(
        db: Session,
        clinic_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[MedicineResponse]:
        query = db.query(Medicine).filter(Medicine.is_active == True)
        if clinic_id:
            query = query.filter(or_(Medicine.clinic_id == clinic_id, Medicine.clinic_id == None))
        if search:
            term = f"%{search}%"
            query = query.filter(or_(Medicine.brand_name.ilike(term), Medicine.generic_name.ilike(term)))
        meds = query.order_by(Medicine.brand_name).limit(100).all()
        return [MedicineResponse.model_validate(m) for m in meds]

    @staticmethod
    def create_medicine(
        db: Session,
        clinic_id: Optional[str],
        data: MedicineCreate,
        actor_id: str
    ) -> MedicineResponse:
        med = Medicine(
            clinic_id=clinic_id,
            brand_name=data.brand_name,
            generic_name=data.generic_name,
            strength=data.strength,
            dosage_form=data.dosage_form.upper(),
            manufacturer=data.manufacturer,
            category=data.category.upper(),
            hsn_code=data.hsn_code,
            gst_rate_percent=data.gst_rate_percent,
            unit_price=data.unit_price,
            is_active=True,
        )
        db.add(med)
        db.commit()
        db.refresh(med)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id or "default",
            action="MEDICINE_CREATE",
            entity_type="Medicine",
            entity_id=med.id,
            details={"brand_name": med.brand_name, "generic_name": med.generic_name}
        )
        return MedicineResponse.model_validate(med)

    @staticmethod
    def create_prescription(
        db: Session,
        clinic_id: str,
        doctor_id: str,
        data: PrescriptionCreate,
        actor_id: str
    ) -> PrescriptionResponse:
        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        rx_num = PrescriptionService.generate_prescription_number(db)

        prescription = Prescription(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            doctor_id=doctor_id,
            appointment_id=data.appointment_id,
            consultation_id=data.consultation_id,
            prescription_number=rx_num,
            status="DRAFT",
            diagnosis_summary=data.diagnosis_summary,
            general_advice=data.general_advice,
            diet_lifestyle_notes=data.diet_lifestyle_notes,
            follow_up_date=data.follow_up_date,
            is_finalized=False,
        )
        db.add(prescription)
        db.flush()

        for it in data.items:
            item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_id=it.medicine_id,
                medicine_name=it.medicine_name,
                generic_name=it.generic_name,
                dosage_form=it.dosage_form.upper(),
                strength=it.strength,
                dosage=it.dosage,
                frequency=it.frequency,
                duration=it.duration,
                route=it.route.upper(),
                instructions=it.instructions,
                quantity=it.quantity,
            )
            db.add(item)

        db.commit()
        db.refresh(prescription)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PRESCRIPTION_CREATE",
            entity_type="Prescription",
            entity_id=prescription.id,
            details={"prescription_number": rx_num, "item_count": len(data.items)}
        )
        return PrescriptionService._format_prescription(prescription)

    @staticmethod
    def finalize_prescription(
        db: Session,
        prescription_id: str,
        clinic_id: str,
        actor_id: str
    ) -> PrescriptionResponse:
        p = db.query(Prescription).filter(
            Prescription.id == prescription_id,
            Prescription.clinic_id == clinic_id
        ).first()

        if not p:
            raise ValueError("Prescription not found or unauthorized")

        if p.is_finalized:
            return PrescriptionService._format_prescription(p)

        p.is_finalized = True
        p.status = "ISSUED"
        p.finalized_at = datetime.now(timezone.utc)
        p.finalized_by_user_id = actor_id
        p.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(p)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PRESCRIPTION_FINALIZE",
            entity_type="Prescription",
            entity_id=p.id,
            details={"prescription_number": p.prescription_number, "finalized_by": actor_id}
        )
        return PrescriptionService._format_prescription(p)

    @staticmethod
    def get_prescription(
        db: Session,
        prescription_id: str,
        clinic_id: Optional[str] = None
    ) -> Optional[PrescriptionResponse]:
        query = db.query(Prescription).filter(Prescription.id == prescription_id)
        if clinic_id:
            query = query.filter(Prescription.clinic_id == clinic_id)
        p = query.first()
        if not p:
            return None
        return PrescriptionService._format_prescription(p)

    @staticmethod
    def list_patient_prescriptions(
        db: Session,
        patient_id: str,
        clinic_id: Optional[str] = None,
        finalized_only: bool = False
    ) -> List[PrescriptionResponse]:
        query = db.query(Prescription).filter(Prescription.patient_id == patient_id)
        if clinic_id:
            query = query.filter(Prescription.clinic_id == clinic_id)
        if finalized_only:
            query = query.filter(Prescription.is_finalized == True)

        rx_list = query.order_by(desc(Prescription.created_at)).all()
        return [PrescriptionService._format_prescription(p) for p in rx_list]


prescription_service = PrescriptionService()
