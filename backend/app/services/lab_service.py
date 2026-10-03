from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.models.lab import LabTest, LabOrder, LabSample, LabResult, LabReport
from app.models.report import Report
from app.models.user import Patient, Doctor, User
from app.models.clinic import Clinic
from app.schemas.lab import (
    LabTestCreate,
    LabTestResponse,
    LabSampleResponse,
    LabResultEntryCreate,
    LabResultResponse,
    LabOrderCreate,
    LabOrderResponse,
    LabReportResponse,
)
from app.services.audit_service import audit_service


class LabService:
    @staticmethod
    def generate_order_number(db: Session) -> str:
        now = datetime.now(timezone.utc)
        prefix = f"LAB-{now.strftime('%Y%m')}-"
        count = db.query(LabOrder).filter(LabOrder.order_number.like(f"{prefix}%")).count()
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def generate_report_number(db: Session) -> str:
        now = datetime.now(timezone.utc)
        prefix = f"LRP-{now.strftime('%Y%m')}-"
        count = db.query(LabReport).filter(LabReport.report_number.like(f"{prefix}%")).count()
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def generate_barcode() -> str:
        return f"SMP-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _format_order(o: LabOrder) -> LabOrderResponse:
        tests_resp = [LabTestResponse.model_validate(t) for t in o.tests]
        samples_resp = []
        for s in o.samples:
            col_name = s.collector.full_name if s.collector else None
            samples_resp.append(LabSampleResponse(
                id=s.id,
                lab_order_id=s.lab_order_id,
                barcode_number=s.barcode_number,
                sample_type=s.sample_type,
                status=s.status,
                rejection_reason=s.rejection_reason,
                collected_at=s.collected_at,
                collected_by_name=col_name,
                created_at=s.created_at,
            ))

        results_resp = []
        for r in o.results:
            tech_name = r.technician.full_name if r.technician else None
            test_name = r.test.name if r.test else None
            results_resp.append(LabResultResponse(
                id=r.id,
                lab_order_id=r.lab_order_id,
                lab_test_id=r.lab_test_id,
                test_name=test_name,
                parameter_name=r.parameter_name,
                result_value=r.result_value,
                unit=r.unit,
                reference_range=r.reference_range,
                is_abnormal=r.is_abnormal,
                technician_notes=r.technician_notes,
                tested_by_name=tech_name,
                created_at=r.created_at,
            ))

        report_resp = None
        if o.report:
            val_name = o.report.validator.full_name if o.report.validator else None
            clinic_name = o.clinic.name if o.clinic else None
            clinic_addr = o.clinic.address if o.clinic else None
            pat_name = o.patient.user.full_name if (o.patient and o.patient.user) else None
            doc_name = o.doctor.user.full_name if (o.doctor and o.doctor.user) else None

            report_resp = LabReportResponse(
                id=o.report.id,
                report_number=o.report.report_number,
                lab_order_id=o.report.lab_order_id,
                clinic_id=o.report.clinic_id,
                clinic_name=clinic_name,
                clinic_address=clinic_addr,
                patient_id=o.report.patient_id,
                patient_name=pat_name,
                doctor_name=doc_name,
                is_validated=o.report.is_validated,
                validated_at=o.report.validated_at,
                validated_by_name=val_name,
                is_released=o.report.is_released,
                released_at=o.report.released_at,
                summary_notes=o.report.summary_notes,
                results=results_resp,
                created_at=o.report.created_at,
            )

        patient_name = o.patient.user.full_name if (o.patient and o.patient.user) else None
        doctor_name = o.doctor.user.full_name if (o.doctor and o.doctor.user) else None

        return LabOrderResponse(
            id=o.id,
            order_number=o.order_number,
            clinic_id=o.clinic_id,
            patient_id=o.patient_id,
            patient_name=patient_name,
            doctor_id=o.doctor_id,
            doctor_name=doctor_name,
            appointment_id=o.appointment_id,
            priority=o.priority,
            status=o.status,
            clinical_notes=o.clinical_notes,
            tests=tests_resp,
            samples=samples_resp,
            results=results_resp,
            report=report_resp,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )

    @staticmethod
    def create_lab_test(
        db: Session,
        clinic_id: Optional[str],
        data: LabTestCreate,
        actor_id: str
    ) -> LabTestResponse:
        test = LabTest(
            clinic_id=clinic_id,
            name=data.name,
            code=data.code.upper(),
            category=data.category.upper(),
            sample_type=data.sample_type,
            turnaround_hours=data.turnaround_hours,
            price=data.price,
            normal_range=data.normal_range,
            unit=data.unit,
            is_active=True,
        )
        db.add(test)
        db.commit()
        db.refresh(test)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id or "default",
            action="LAB_TEST_CREATE",
            entity_type="LabTest",
            entity_id=test.id,
            details={"name": test.name, "code": test.code}
        )
        return LabTestResponse.model_validate(test)

    @staticmethod
    def list_lab_tests(
        db: Session,
        clinic_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[LabTestResponse]:
        query = db.query(LabTest).filter(LabTest.is_active == True)
        if clinic_id:
            query = query.filter(or_(LabTest.clinic_id == clinic_id, LabTest.clinic_id == None))
        if category:
            query = query.filter(LabTest.category == category.upper())
        if search:
            term = f"%{search}%"
            query = query.filter(or_(LabTest.name.ilike(term), LabTest.code.ilike(term)))
        tests = query.order_by(LabTest.name).all()
        return [LabTestResponse.model_validate(t) for t in tests]

    @staticmethod
    def create_lab_order(
        db: Session,
        clinic_id: str,
        doctor_id: str,
        data: LabOrderCreate,
        actor_id: str
    ) -> LabOrderResponse:
        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        order_num = LabService.generate_order_number(db)
        order = LabOrder(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            doctor_id=doctor_id,
            appointment_id=data.appointment_id,
            order_number=order_num,
            priority=data.priority.upper(),
            status="ORDERED",
            clinical_notes=data.clinical_notes,
        )
        db.add(order)
        db.flush()

        # Attach tests from catalog
        tests = db.query(LabTest).filter(LabTest.id.in_(data.test_ids)).all()
        order.tests = tests

        # Generate sample tracking entry
        sample_types = list(set(t.sample_type for t in tests)) if tests else ["Whole Blood"]
        for st in sample_types:
            sample = LabSample(
                lab_order_id=order.id,
                barcode_number=LabService.generate_barcode(),
                sample_type=st,
                status="PENDING",
            )
            db.add(sample)

        db.commit()
        db.refresh(order)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="LAB_ORDER_CREATE",
            entity_type="LabOrder",
            entity_id=order.id,
            details={"order_number": order_num, "test_count": len(tests)}
        )
        return LabService._format_order(order)

    @staticmethod
    def collect_sample(
        db: Session,
        sample_id: str,
        clinic_id: str,
        actor_id: str
    ) -> LabOrderResponse:
        sample = db.query(LabSample).filter(LabSample.id == sample_id).first()
        if not sample:
            raise ValueError("Sample not found")

        order = db.query(LabOrder).filter(
            LabOrder.id == sample.lab_order_id,
            LabOrder.clinic_id == clinic_id
        ).first()
        if not order:
            raise ValueError("Lab order not found or unauthorized")

        sample.status = "COLLECTED"
        sample.collected_at = datetime.now(timezone.utc)
        sample.collected_by_user_id = actor_id

        order.status = "SAMPLE_COLLECTED"
        db.commit()
        db.refresh(order)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="LAB_SAMPLE_COLLECT",
            entity_type="LabSample",
            entity_id=sample.id,
            details={"barcode": sample.barcode_number}
        )
        return LabService._format_order(order)

    @staticmethod
    def enter_results(
        db: Session,
        order_id: str,
        clinic_id: str,
        results_data: List[LabResultEntryCreate],
        actor_id: str
    ) -> LabOrderResponse:
        order = db.query(LabOrder).filter(
            LabOrder.id == order_id,
            LabOrder.clinic_id == clinic_id
        ).first()
        if not order:
            raise ValueError("Lab order not found or unauthorized")

        # Clear existing unvalidated results if re-entering
        db.query(LabResult).filter(LabResult.lab_order_id == order.id).delete()

        for rd in results_data:
            res = LabResult(
                lab_order_id=order.id,
                lab_test_id=rd.lab_test_id,
                parameter_name=rd.parameter_name,
                result_value=rd.result_value,
                unit=rd.unit,
                reference_range=rd.reference_range,
                is_abnormal=rd.is_abnormal,
                technician_notes=rd.technician_notes,
                tested_by_user_id=actor_id,
            )
            db.add(res)

        order.status = "RESULT_READY"
        db.commit()
        db.refresh(order)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="LAB_RESULT_ENTRY",
            entity_type="LabOrder",
            entity_id=order.id,
            details={"result_count": len(results_data)}
        )
        return LabService._format_order(order)

    @staticmethod
    def validate_and_release_report(
        db: Session,
        order_id: str,
        clinic_id: str,
        summary_notes: Optional[str],
        actor_id: str
    ) -> LabReportResponse:
        order = db.query(LabOrder).filter(
            LabOrder.id == order_id,
            LabOrder.clinic_id == clinic_id
        ).first()
        if not order:
            raise ValueError("Lab order not found or unauthorized")

        if not order.results:
            raise ValueError("Cannot release lab report without entered test results")

        now = datetime.now(timezone.utc)
        rep_num = LabService.generate_report_number(db)

        report = db.query(LabReport).filter(LabReport.lab_order_id == order.id).first()
        if not report:
            report = LabReport(
                clinic_id=clinic_id,
                lab_order_id=order.id,
                patient_id=order.patient_id,
                report_number=rep_num,
                is_validated=True,
                validated_at=now,
                validated_by_user_id=actor_id,
                is_released=True,
                released_at=now,
                summary_notes=summary_notes,
            )
            db.add(report)
        else:
            report.is_validated = True
            report.validated_at = now
            report.validated_by_user_id = actor_id
            report.is_released = True
            report.released_at = now
            report.summary_notes = summary_notes

        order.status = "VALIDATED"

        # Also create a corresponding patient-facing Report in the existing reports table
        test_names = ", ".join(t.name for t in order.tests) if order.tests else "Diagnostic Panel"
        legacy_report = db.query(Report).filter(
            Report.patient_id == order.patient_id,
            Report.title.like(f"%{order.order_number}%")
        ).first()
        if not legacy_report:
            legacy_report = Report(
                clinic_id=clinic_id,
                patient_id=order.patient_id,
                doctor_id=order.doctor_id,
                title=f"Lab Diagnostic Report ({test_names}) - {order.order_number}",
                report_type="Pathology",
                status="ready",
                notes=summary_notes,
                report_date=now.date(),
            )
            db.add(legacy_report)

        db.commit()
        db.refresh(report)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="LAB_REPORT_RELEASE",
            entity_type="LabReport",
            entity_id=report.id,
            details={"report_number": report.report_number, "order_number": order.order_number}
        )

        formatted_order = LabService._format_order(order)
        return formatted_order.report

    @staticmethod
    def get_lab_order(
        db: Session,
        order_id: str,
        clinic_id: Optional[str] = None
    ) -> Optional[LabOrderResponse]:
        query = db.query(LabOrder).filter(LabOrder.id == order_id)
        if clinic_id:
            query = query.filter(LabOrder.clinic_id == clinic_id)
        order = query.first()
        if not order:
            return None
        return LabService._format_order(order)

    @staticmethod
    def list_orders(
        db: Session,
        clinic_id: str,
        patient_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LabOrderResponse]:
        query = db.query(LabOrder).filter(LabOrder.clinic_id == clinic_id)
        if patient_id:
            query = query.filter(LabOrder.patient_id == patient_id)
        if status:
            query = query.filter(LabOrder.status == status.upper())
        orders = query.order_by(desc(LabOrder.created_at)).all()
        return [LabService._format_order(o) for o in orders]


lab_service = LabService()
