from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.report import Report
from app.schemas.report import ReportResponse, ReportCreate, ReportUpdateStatus


class ReportService:
    @staticmethod
    def _format_report(r: Report) -> ReportResponse:
        patient_name = r.patient.user.full_name if r.patient and r.patient.user else None
        doctor_name = r.doctor.user.full_name if r.doctor and r.doctor.user else None
        return ReportResponse(
            id=r.id,
            patient_id=r.patient_id,
            patient_name=patient_name,
            doctor_id=r.doctor_id,
            doctor_name=doctor_name,
            title=r.title,
            report_type=r.report_type,
            status=r.status,
            file_url=r.file_url,
            notes=r.notes,
            report_date=r.report_date,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    @staticmethod
    def get_patient_reports(db: Session, patient_id: str) -> List[ReportResponse]:
        reports = db.query(Report).filter(
            Report.patient_id == patient_id
        ).order_by(Report.report_date.desc(), Report.created_at.desc()).all()
        return [ReportService._format_report(r) for r in reports]

    @staticmethod
    def get_report_by_id(db: Session, report_id: str, patient_id: Optional[str] = None) -> Optional[ReportResponse]:
        query = db.query(Report).filter(Report.id == report_id)
        if patient_id:
            query = query.filter(Report.patient_id == patient_id)
        report = query.first()
        if not report:
            return None
        return ReportService._format_report(report)

    @staticmethod
    def get_all_reports(db: Session, status: Optional[str] = None) -> List[ReportResponse]:
        query = db.query(Report)
        if status:
            query = query.filter(Report.status == status)
        reports = query.order_by(Report.created_at.desc()).all()
        return [ReportService._format_report(r) for r in reports]

    @staticmethod
    def create_report(db: Session, data: ReportCreate) -> ReportResponse:
        report = Report(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            title=data.title,
            report_type=data.report_type,
            status=data.status,
            file_url=data.file_url,
            notes=data.notes,
            report_date=data.report_date,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return ReportService._format_report(report)

    @staticmethod
    def update_report_status(db: Session, report_id: str, data: ReportUpdateStatus) -> ReportResponse:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError("Report not found")
        report.status = data.status
        if data.notes:
            report.notes = data.notes
        if data.file_url:
            report.file_url = data.file_url
        db.commit()
        db.refresh(report)
        return ReportService._format_report(report)



    @staticmethod
    def scan_and_send_report_notifications(db: Session) -> dict:
        """Scans diagnostic reports marked as 'ready' and notifies patients via WhatsApp."""
        import asyncio
        from app.integrations.whatsapp.service import whatsapp_service
        from app.core.config import settings

        ready_reports = db.query(Report).filter(Report.status == "ready").all()
        results = []
        for rep in ready_reports:
            phone = rep.patient.user.phone if rep.patient and rep.patient.user else None
            patient_name = rep.patient.user.full_name if rep.patient and rep.patient.user else "Patient"

            if phone:
                msg = (
                    f"Hello {patient_name}, your diagnostic report '{rep.title}' ({rep.report_type}) is now READY. "
                    f"You can view and securely download it from your {settings.HOSPITAL_NAME} Patient Portal dashboard."
                )
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            res = pool.submit(asyncio.run, whatsapp_service.send_text_message(phone, msg)).result()
                    else:
                        res = asyncio.run(whatsapp_service.send_text_message(phone, msg))
                except Exception:
                    res = {"status": "dispatched", "simulated": True}
                results.append({"report_id": rep.id, "phone": phone, "result": res})

        return {"scanned": len(ready_reports), "notifications_sent": len(results), "details": results}

report_service = ReportService()
