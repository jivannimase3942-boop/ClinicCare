from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, Patient, Doctor, Department
from app.models.appointment import Appointment
from app.models.visit import VisitHistory
from app.schemas.patient import (
    PatientProfileResponse,
    PatientProfileUpdate,
    VisitHistoryResponse,
    VisitHistoryCreate,
)


class PatientService:
    @staticmethod
    def _format_patient_profile(p: Patient) -> PatientProfileResponse:
        return PatientProfileResponse(
            id=p.id,
            user_id=p.user_id,
            full_name=p.user.full_name if p.user else "Patient",
            email=p.user.email if p.user else "",
            phone=p.user.phone if p.user else None,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            blood_group=p.blood_group,
            address=p.address,
            emergency_contact=p.emergency_contact,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def search_patients(
        db: Session,
        query_str: Optional[str] = None,
        blood_group: Optional[str] = None,
        gender: Optional[str] = None,
        limit: int = 50
    ) -> List[PatientProfileResponse]:
        query = db.query(Patient).join(User, Patient.user_id == User.id)
        if query_str and query_str.strip():
            s = f"%{query_str.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(s),
                    User.email.ilike(s),
                    User.phone.ilike(s),
                    Patient.id.ilike(s),
                    Patient.blood_group.ilike(s),
                    Patient.address.ilike(s),
                )
            )
        if blood_group and blood_group.strip():
            query = query.filter(Patient.blood_group == blood_group.strip().upper())
        if gender and gender.strip():
            query = query.filter(Patient.gender == gender.strip().lower())

        patients = query.order_by(Patient.created_at.desc()).limit(limit).all()
        return [PatientService._format_patient_profile(p) for p in patients]

    @staticmethod
    def get_patient_by_id(db: Session, patient_id: str) -> Optional[PatientProfileResponse]:
        p = db.query(Patient).filter(Patient.id == patient_id).first()
        if not p:
            return None
        return PatientService._format_patient_profile(p)

    @staticmethod
    def update_patient_profile(
        db: Session,
        patient_id: str,
        data: PatientProfileUpdate
    ) -> PatientProfileResponse:
        p = db.query(Patient).filter(Patient.id == patient_id).first()
        if not p:
            raise ValueError("Patient not found")

        if data.full_name and p.user:
            p.user.full_name = data.full_name
        if data.phone and p.user:
            p.user.phone = data.phone
        if data.date_of_birth is not None:
            p.date_of_birth = data.date_of_birth
        if data.gender is not None:
            p.gender = data.gender
        if data.blood_group is not None:
            p.blood_group = data.blood_group
        if data.address is not None:
            p.address = data.address
        if data.emergency_contact is not None:
            p.emergency_contact = data.emergency_contact

        db.commit()
        db.refresh(p)
        return PatientService._format_patient_profile(p)

    @staticmethod
    def _format_visit(v: VisitHistory) -> VisitHistoryResponse:
        doc_name = v.doctor.user.full_name if v.doctor and v.doctor.user else None
        dept_name = v.department.name if v.department else None
        pat_name = v.patient.user.full_name if v.patient and v.patient.user else None

        return VisitHistoryResponse(
            id=v.id,
            patient_id=v.patient_id,
            patient_name=pat_name,
            doctor_id=v.doctor_id,
            doctor_name=doc_name,
            department_id=v.department_id,
            department_name=dept_name,
            appointment_id=v.appointment_id,
            visit_date=v.visit_date,
            visit_type=v.visit_type,
            visit_status=v.visit_status,
            vitals_summary=v.vitals_summary,
            administrative_notes=v.administrative_notes,
            follow_up_instructions=v.follow_up_instructions,
            created_at=v.created_at,
        )

    @staticmethod
    def get_patient_visits(
        db: Session,
        patient_id: Optional[str] = None
    ) -> List[VisitHistoryResponse]:
        query = db.query(VisitHistory)
        if patient_id:
            query = query.filter(VisitHistory.patient_id == patient_id)
        visits = query.order_by(VisitHistory.visit_date.desc()).all()
        return [PatientService._format_visit(v) for v in visits]

    @staticmethod
    def record_visit(
        db: Session,
        data: VisitHistoryCreate
    ) -> VisitHistoryResponse:
        v = VisitHistory(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department_id=data.department_id,
            appointment_id=data.appointment_id,
            visit_date=data.visit_date,
            visit_type=data.visit_type or "OPD Consultation",
            visit_status=data.visit_status or "completed",
            vitals_summary=data.vitals_summary,
            administrative_notes=data.administrative_notes,
            follow_up_instructions=data.follow_up_instructions,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return PatientService._format_visit(v)


patient_service = PatientService()
