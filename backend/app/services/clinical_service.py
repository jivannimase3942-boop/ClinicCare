from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.clinical import ConsultationRecord, VitalSign, ClinicalDocument
from app.models.user import Patient, Doctor, User
from app.models.appointment import Appointment
from app.models.report import Report
from app.schemas.clinical import (
    VitalSignCreate,
    VitalSignResponse,
    ConsultationRecordCreate,
    ConsultationRecordUpdate,
    ConsultationRecordResponse,
    ClinicalDocumentCreate,
    ClinicalDocumentResponse,
    PatientTimelineResponse,
    TimelineItem,
)
from app.services.audit_service import audit_service


class ClinicalService:
    @staticmethod
    def _calculate_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
        if weight_kg and height_cm and height_cm > 0:
            height_m = height_cm / 100.0
            return round(weight_kg / (height_m * height_m), 1)
        return None

    @staticmethod
    def _format_consultation(rec: ConsultationRecord) -> ConsultationRecordResponse:
        vitals_resp = [VitalSignResponse.model_validate(v) for v in (rec.vitals or [])]
        patient_name = rec.patient.user.full_name if (rec.patient and rec.patient.user) else None
        doctor_name = rec.doctor.user.full_name if (rec.doctor and rec.doctor.user) else None
        doctor_spec = rec.doctor.specialization if rec.doctor else None

        return ConsultationRecordResponse(
            id=rec.id,
            clinic_id=rec.clinic_id,
            patient_id=rec.patient_id,
            patient_name=patient_name,
            doctor_id=rec.doctor_id,
            doctor_name=doctor_name,
            doctor_specialization=doctor_spec,
            appointment_id=rec.appointment_id,
            status=rec.status,
            version=rec.version,
            chief_complaint=rec.chief_complaint,
            history_of_present_illness=rec.history_of_present_illness,
            medical_history=rec.medical_history,
            allergies=rec.allergies,
            lifestyle_notes=rec.lifestyle_notes,
            examination_notes=rec.examination_notes,
            diagnosis=rec.diagnosis,
            treatment_plan=rec.treatment_plan,
            investigations_ordered=rec.investigations_ordered,
            follow_up_date=rec.follow_up_date,
            referral=rec.referral,
            clinical_notes=rec.clinical_notes,
            is_finalized=rec.is_finalized,
            finalized_at=rec.finalized_at,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            vitals=vitals_resp,
        )

    @staticmethod
    def record_vitals(
        db: Session,
        clinic_id: str,
        data: VitalSignCreate,
        actor_id: str
    ) -> VitalSignResponse:
        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        bmi = ClinicalService._calculate_bmi(data.weight_kg, data.height_cm)

        vital = VitalSign(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            consultation_id=data.consultation_id,
            appointment_id=data.appointment_id,
            recorded_by_user_id=actor_id,
            temperature_celsius=data.temperature_celsius,
            pulse_bpm=data.pulse_bpm,
            bp_systolic=data.bp_systolic,
            bp_diastolic=data.bp_diastolic,
            respiratory_rate=data.respiratory_rate,
            spo2_percent=data.spo2_percent,
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            bmi=bmi,
            notes=data.notes,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(vital)
        db.commit()
        db.refresh(vital)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="VITAL_RECORD",
            entity_type="VitalSign",
            entity_id=vital.id,
            details={
                "patient_id": data.patient_id,
                "bp": f"{data.bp_systolic}/{data.bp_diastolic}" if data.bp_systolic else None,
                "pulse": data.pulse_bpm,
                "spo2": data.spo2_percent,
            }
        )
        return VitalSignResponse.model_validate(vital)

    @staticmethod
    def get_patient_vitals(
        db: Session,
        patient_id: str,
        clinic_id: Optional[str] = None
    ) -> List[VitalSignResponse]:
        query = db.query(VitalSign).filter(VitalSign.patient_id == patient_id)
        if clinic_id:
            query = query.filter(VitalSign.clinic_id == clinic_id)
        vitals = query.order_by(desc(VitalSign.recorded_at)).all()
        return [VitalSignResponse.model_validate(v) for v in vitals]

    @staticmethod
    def create_consultation(
        db: Session,
        clinic_id: str,
        doctor_id: str,
        data: ConsultationRecordCreate,
        actor_id: str
    ) -> ConsultationRecordResponse:
        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        consultation = ConsultationRecord(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            doctor_id=doctor_id,
            appointment_id=data.appointment_id,
            status="DRAFT",
            version=1,
            chief_complaint=data.chief_complaint,
            history_of_present_illness=data.history_of_present_illness,
            medical_history=data.medical_history,
            allergies=data.allergies,
            lifestyle_notes=data.lifestyle_notes,
            examination_notes=data.examination_notes,
            diagnosis=data.diagnosis,
            treatment_plan=data.treatment_plan,
            investigations_ordered=data.investigations_ordered,
            follow_up_date=data.follow_up_date,
            referral=data.referral,
            clinical_notes=data.clinical_notes,
            is_finalized=False,
        )
        db.add(consultation)
        db.commit()
        db.refresh(consultation)

        # Record embedded vitals if provided
        if data.vitals:
            data.vitals.consultation_id = consultation.id
            data.vitals.patient_id = data.patient_id
            ClinicalService.record_vitals(db, clinic_id, data.vitals, actor_id)
            db.refresh(consultation)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="CONSULTATION_CREATE",
            entity_type="ConsultationRecord",
            entity_id=consultation.id,
            details={"patient_id": data.patient_id, "status": "DRAFT", "diagnosis": data.diagnosis}
        )
        return ClinicalService._format_consultation(consultation)

    @staticmethod
    def update_consultation(
        db: Session,
        consultation_id: str,
        clinic_id: str,
        data: ConsultationRecordUpdate,
        actor_id: str
    ) -> ConsultationRecordResponse:
        consultation = db.query(ConsultationRecord).filter(
            ConsultationRecord.id == consultation_id,
            ConsultationRecord.clinic_id == clinic_id
        ).first()

        if not consultation:
            raise ValueError("Consultation record not found or unauthorized")

        if consultation.is_finalized:
            raise ValueError("Finalized clinical records cannot be overwritten. Preserving medical record integrity.")

        # Update provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(consultation, key, val)

        consultation.version += 1
        consultation.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(consultation)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="CONSULTATION_UPDATE",
            entity_type="ConsultationRecord",
            entity_id=consultation.id,
            details={"version": consultation.version}
        )
        return ClinicalService._format_consultation(consultation)

    @staticmethod
    def finalize_consultation(
        db: Session,
        consultation_id: str,
        clinic_id: str,
        actor_id: str
    ) -> ConsultationRecordResponse:
        consultation = db.query(ConsultationRecord).filter(
            ConsultationRecord.id == consultation_id,
            ConsultationRecord.clinic_id == clinic_id
        ).first()

        if not consultation:
            raise ValueError("Consultation record not found or unauthorized")

        if consultation.is_finalized:
            return ClinicalService._format_consultation(consultation)

        consultation.is_finalized = True
        consultation.status = "FINALIZED"
        consultation.finalized_at = datetime.now(timezone.utc)
        consultation.finalized_by_user_id = actor_id
        consultation.updated_at = datetime.now(timezone.utc)

        # If linked to an appointment, complete the consultation in OPD
        if consultation.appointment_id:
            appt = db.query(Appointment).filter(Appointment.id == consultation.appointment_id).first()
            if appt:
                appt.status = "completed"
                appt.queue_status = "COMPLETED"
                appt.consultation_ended_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(consultation)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="CONSULTATION_FINALIZE",
            entity_type="ConsultationRecord",
            entity_id=consultation.id,
            details={"version": consultation.version, "finalized_by": actor_id}
        )
        return ClinicalService._format_consultation(consultation)

    @staticmethod
    def get_consultation(
        db: Session,
        consultation_id: str,
        clinic_id: Optional[str] = None
    ) -> Optional[ConsultationRecordResponse]:
        query = db.query(ConsultationRecord).filter(ConsultationRecord.id == consultation_id)
        if clinic_id:
            query = query.filter(ConsultationRecord.clinic_id == clinic_id)
        rec = query.first()
        if not rec:
            return None
        return ClinicalService._format_consultation(rec)

    @staticmethod
    def list_patient_consultations(
        db: Session,
        patient_id: str,
        clinic_id: Optional[str] = None,
        finalized_only: bool = False
    ) -> List[ConsultationRecordResponse]:
        query = db.query(ConsultationRecord).filter(ConsultationRecord.patient_id == patient_id)
        if clinic_id:
            query = query.filter(ConsultationRecord.clinic_id == clinic_id)
        if finalized_only:
            query = query.filter(ConsultationRecord.is_finalized == True)

        records = query.order_by(desc(ConsultationRecord.created_at)).all()
        return [ClinicalService._format_consultation(r) for r in records]

    @staticmethod
    def create_document(
        db: Session,
        clinic_id: str,
        data: ClinicalDocumentCreate,
        actor_id: str
    ) -> ClinicalDocumentResponse:
        doc = ClinicalDocument(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            consultation_id=data.consultation_id,
            uploaded_by_user_id=actor_id,
            document_type=data.document_type,
            title=data.title,
            file_url=data.file_url,
            file_type=data.file_type,
            file_size_bytes=data.file_size_bytes,
            description=data.description,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="CLINICAL_DOCUMENT_UPLOAD",
            entity_type="ClinicalDocument",
            entity_id=doc.id,
            details={"title": data.title, "patient_id": data.patient_id}
        )
        return ClinicalDocumentResponse.model_validate(doc)

    @staticmethod
    def get_patient_timeline(
        db: Session,
        patient_id: str,
        clinic_id: str,
        is_patient_user: bool = False
    ) -> PatientTimelineResponse:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        events: List[TimelineItem] = []

        # 1. Consultations
        consult_query = db.query(ConsultationRecord).filter(
            ConsultationRecord.patient_id == patient_id,
            ConsultationRecord.clinic_id == clinic_id
        )
        if is_patient_user:
            consult_query = consult_query.filter(ConsultationRecord.is_finalized == True)

        for c in consult_query.all():
            doc_name = c.doctor.user.full_name if (c.doctor and c.doctor.user) else None
            events.append(TimelineItem(
                event_type="CONSULTATION",
                event_id=c.id,
                timestamp=c.finalized_at or c.created_at,
                title=f"Clinical Consultation: {c.diagnosis}",
                subtitle=f"Chief complaint: {c.chief_complaint}",
                status=c.status,
                doctor_name=doc_name,
                details={
                    "treatment_plan": c.treatment_plan,
                    "follow_up_date": str(c.follow_up_date) if c.follow_up_date else None,
                    "is_finalized": c.is_finalized,
                }
            ))

        # 2. Vitals
        vitals_query = db.query(VitalSign).filter(
            VitalSign.patient_id == patient_id,
            VitalSign.clinic_id == clinic_id
        )
        for v in vitals_query.all():
            summary_parts = []
            if v.bp_systolic and v.bp_diastolic:
                summary_parts.append(f"BP: {v.bp_systolic}/{v.bp_diastolic} mmHg")
            if v.pulse_bpm:
                summary_parts.append(f"Pulse: {v.pulse_bpm} bpm")
            if v.spo2_percent:
                summary_parts.append(f"SpO2: {v.spo2_percent}%")
            if v.temperature_celsius:
                summary_parts.append(f"Temp: {v.temperature_celsius}°C")

            events.append(TimelineItem(
                event_type="VITAL_SIGN",
                event_id=v.id,
                timestamp=v.recorded_at,
                title="Vitals Recorded",
                subtitle=", ".join(summary_parts) if summary_parts else "Routine vitals",
                status="RECORDED",
                details={
                    "bmi": v.bmi,
                    "weight_kg": v.weight_kg,
                    "height_cm": v.height_cm,
                }
            ))

        # 3. Appointments
        appt_query = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.clinic_id == clinic_id
        )
        for a in appt_query.all():
            doc_name = a.doctor.user.full_name if (a.doctor and a.doctor.user) else None
            dept_name = a.doctor.department.name if (a.doctor and a.doctor.department) else None
            events.append(TimelineItem(
                event_type="APPOINTMENT",
                event_id=a.id,
                timestamp=datetime.combine(a.appointment_date, datetime.min.time()),
                title=f"OPD Encounter ({a.status})",
                subtitle=f"Time: {a.appointment_time} • Token: {a.token_number or 'N/A'}",
                status=a.status,
                doctor_name=doc_name,
                department_name=dept_name,
                details={
                    "queue_status": a.queue_status,
                    "appointment_type": a.appointment_type,
                }
            ))

        # 4. Clinical Documents
        doc_query = db.query(ClinicalDocument).filter(
            ClinicalDocument.patient_id == patient_id,
            ClinicalDocument.clinic_id == clinic_id
        )
        for d in doc_query.all():
            events.append(TimelineItem(
                event_type="DOCUMENT",
                event_id=d.id,
                timestamp=d.created_at,
                title=f"Clinical Document: {d.title}",
                subtitle=f"Type: {d.document_type}",
                status="UPLOADED",
                details={"file_url": d.file_url, "file_type": d.file_type}
            ))

        # Sort all timeline items chronologically descending
        events.sort(key=lambda x: x.timestamp, reverse=True)

        patient_name = patient.user.full_name if (patient and patient.user) else "Patient"
        return PatientTimelineResponse(
            patient_id=patient_id,
            patient_name=patient_name,
            total_events=len(events),
            events=events,
        )


clinical_service = ClinicalService()
