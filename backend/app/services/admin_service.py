from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User, Patient, Doctor, Department
from app.models.appointment import Appointment
from app.models.report import Report
from app.models.feedback import Feedback
from app.models.ai import AIConversation
from app.models.escalation import Escalation
from app.models.error_log import ErrorLog
from app.schemas.admin import AdminDashboardStats, MetricSummary, ChartDataPoint, ErrorLogResponse


class AdminService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> AdminDashboardStats:
        today = date.today()

        # Counts
        total_patients = db.query(func.count(Patient.id)).scalar() or 0
        total_doctors = db.query(func.count(Doctor.id)).filter(Doctor.is_active == True).scalar() or 0
        today_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.appointment_date == today,
            Appointment.status != "cancelled"
        ).scalar() or 0
        upcoming_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.appointment_date >= today,
            Appointment.status.in_(["confirmed", "pending", "rescheduled"])
        ).scalar() or 0
        pending_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.status == "pending"
        ).scalar() or 0
        completed_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.status == "completed"
        ).scalar() or 0
        cancelled_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.status == "cancelled"
        ).scalar() or 0
        pending_reports = db.query(func.count(Report.id)).filter(
            Report.status.in_(["pending", "processing"])
        ).scalar() or 0
        open_escalations = db.query(func.count(Escalation.id)).filter(
            Escalation.status.in_(["open", "assigned", "in_progress"])
        ).scalar() or 0
        
        # Ambulance and blood metrics
        from app.models.ambulance import Ambulance, AmbulanceRequest
        from app.models.blood import BloodInventory
        active_ambulances = db.query(func.count(Ambulance.id)).filter(Ambulance.status == "available").scalar() or 0
        emergency_requests = db.query(func.count(Escalation.id)).filter(
            Escalation.reason == "emergency",
            Escalation.status.in_(["open", "assigned", "in_progress"])
        ).scalar() or 0
        available_blood_units = db.query(func.sum(BloodInventory.units_available)).scalar() or 0

        feedback_count = db.query(func.count(Feedback.id)).scalar() or 0
        avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 0.0
        ai_conv_count = db.query(func.count(AIConversation.id)).scalar() or 0


        # Appointments by Day (Past 7 days up to next 3 days)
        start_date = today - timedelta(days=6)
        apps_by_day = []
        for i in range(10):
            curr = start_date + timedelta(days=i)
            count = db.query(func.count(Appointment.id)).filter(Appointment.appointment_date == curr).scalar() or 0
            apps_by_day.append(ChartDataPoint(label=curr.strftime("%b %d"), value=float(count)))

        # Appointment status distribution
        status_groups = db.query(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status).all()
        app_status_dist = [ChartDataPoint(label=s.capitalize(), value=float(c)) for s, c in status_groups]

        # Feedback ratings distribution
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        fb_groups = db.query(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating).all()
        for r, c in fb_groups:
            if r in rating_counts:
                rating_counts[r] = c
        fb_dist = [ChartDataPoint(label=f"{star} Stars", value=float(cnt)) for star, cnt in rating_counts.items()]

        # Report status distribution
        rep_groups = db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
        rep_dist = [ChartDataPoint(label=s.capitalize(), value=float(c)) for s, c in rep_groups]

        # AI conversations trend (Past 7 days)
        ai_trend = []
        for i in range(7):
            curr = today - timedelta(days=6 - i)
            # Filter by date portion of created_at
            next_d = curr + timedelta(days=1)
            count = db.query(func.count(AIConversation.id)).filter(
                AIConversation.created_at >= datetime.combine(curr, datetime.min.time()),
                AIConversation.created_at < datetime.combine(next_d, datetime.min.time())
            ).scalar() or 0
            ai_trend.append(ChartDataPoint(label=curr.strftime("%b %d"), value=float(count)))

        return AdminDashboardStats(
            metrics=MetricSummary(
                total_patients=total_patients,
                total_doctors=total_doctors,
                today_appointments=today_appointments,
                upcoming_appointments=upcoming_appointments,
                pending_appointments=pending_appointments,
                completed_appointments=completed_appointments,
                cancelled_appointments=cancelled_appointments,
                pending_reports=pending_reports,
                open_escalations=open_escalations,
                active_ambulances=active_ambulances,
                emergency_requests=emergency_requests,
                available_blood_units=available_blood_units,
                feedback_count=feedback_count,
                ai_conversations_count=ai_conv_count,
                average_rating=round(float(avg_rating), 1),
            ),
            appointments_by_day=apps_by_day,
            appointment_status_distribution=app_status_dist,
            feedback_ratings_distribution=fb_dist,
            report_status_distribution=rep_dist,
            ai_conversations_trend=ai_trend,
        )

    @staticmethod
    def get_error_logs(db: Session, limit: int = 50) -> List[ErrorLogResponse]:
        logs = db.query(ErrorLog).order_by(ErrorLog.created_at.desc()).limit(limit).all()
        return [ErrorLogResponse.model_validate(l) for l in logs]

    @staticmethod
    def create_error_log(
        db: Session,
        service_name: Optional[str] = "backend",
        error_level: Optional[str] = "ERROR",
        message: str = "",
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        context_json: Optional[str] = None,
    ) -> ErrorLog:
        log = ErrorLog(
            service_name=service_name or "backend",
            error_level=error_level or "ERROR",
            message=message or "Workflow / system exception",
            stack_trace=stack_trace,
            endpoint=endpoint,
            context_json=context_json,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log


    @staticmethod
    def get_clinical_analytics(db: Session, clinic_id: str) -> Dict[str, Any]:
        """
        Computes tenant-scoped operational analytics across Patients, Doctors, Lab, and Pharmacy.
        """
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # 1. Patient Analytics
        from app.models.clinical import ConsultationRecord
        from app.models.lab import LabOrder
        from app.models.pharmacy import StockBatch
        from app.models.billing import Invoice, InvoiceItem

        # Patients connected to clinic
        total_patients = db.query(func.count(Patient.id)).join(User, Patient.user_id == User.id).filter(
            User.clinic_id == clinic_id
        ).scalar() or 0

        new_patients_30d = db.query(func.count(Patient.id)).join(User, Patient.user_id == User.id).filter(
            User.clinic_id == clinic_id,
            Patient.created_at >= thirty_days_ago
        ).scalar() or 0

        total_apps = db.query(func.count(Appointment.id)).filter(Appointment.clinic_id == clinic_id).scalar() or 0
        completed_apps = db.query(func.count(Appointment.id)).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.status == "completed"
        ).scalar() or 0
        cancelled_apps = db.query(func.count(Appointment.id)).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.status == "cancelled"
        ).scalar() or 0
        noshow_apps = db.query(func.count(Appointment.id)).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.status == "no_show"
        ).scalar() or 0

        # 2. Doctor Analytics
        total_docs = db.query(func.count(Doctor.id)).join(User, Doctor.user_id == User.id).filter(
            User.clinic_id == clinic_id,
            Doctor.is_active == True
        ).scalar() or 0

        doc_consults = db.query(
            Doctor.id,
            func.count(Appointment.id)
        ).join(Appointment, Appointment.doctor_id == Doctor.id).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.status == "completed"
        ).group_by(Doctor.id).all()

        doctor_utilization = []
        for doc_id, c_count in doc_consults:
            doc_obj = db.query(Doctor).filter(Doctor.id == doc_id).first()
            d_name = doc_obj.user.full_name if (doc_obj and doc_obj.user) else "Doctor"
            doctor_utilization.append({"doctor_name": d_name, "consultations_completed": c_count})

        # 3. Lab Analytics
        total_lab_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.clinic_id == clinic_id).scalar() or 0
        pending_lab_orders = db.query(func.count(LabOrder.id)).filter(
            LabOrder.clinic_id == clinic_id,
            LabOrder.status.in_(["ORDERED", "SAMPLE_COLLECTED", "PROCESSING", "RESULT_READY"])
        ).scalar() or 0
        released_lab_reports = db.query(func.count(LabOrder.id)).filter(
            LabOrder.clinic_id == clinic_id,
            LabOrder.status == "VALIDATED"
        ).scalar() or 0

        # 4. Pharmacy Analytics
        active_batches = db.query(func.count(StockBatch.id)).filter(
            StockBatch.clinic_id == clinic_id,
            StockBatch.is_active == True
        ).scalar() or 0

        low_stock_count = db.query(func.count(StockBatch.id)).filter(
            StockBatch.clinic_id == clinic_id,
            StockBatch.is_active == True,
            StockBatch.current_quantity <= StockBatch.reorder_threshold
        ).scalar() or 0

        expired_count = db.query(func.count(StockBatch.id)).filter(
            StockBatch.clinic_id == clinic_id,
            StockBatch.is_active == True,
            StockBatch.current_quantity > 0,
            StockBatch.expiry_date < today
        ).scalar() or 0

        near_expiry_cutoff = today + timedelta(days=60)
        near_expiry_count = db.query(func.count(StockBatch.id)).filter(
            StockBatch.clinic_id == clinic_id,
            StockBatch.is_active == True,
            StockBatch.current_quantity > 0,
            StockBatch.expiry_date >= today,
            StockBatch.expiry_date <= near_expiry_cutoff
        ).scalar() or 0

        pharmacy_sales_total = db.query(func.sum(InvoiceItem.total_price)).join(Invoice, InvoiceItem.invoice_id == Invoice.id).filter(
            Invoice.clinic_id == clinic_id,
            InvoiceItem.item_type == "MEDICINE"
        ).scalar() or 0.0

        return {
            "clinic_id": clinic_id,
            "generated_at": datetime.now().isoformat(),
            "patient_metrics": {
                "total_patients": total_patients,
                "new_patients_30d": new_patients_30d,
                "appointments_total": total_apps,
                "completed_consultations": completed_apps,
                "cancellations": cancelled_apps,
                "no_shows": noshow_apps,
            },
            "doctor_metrics": {
                "active_doctors": total_docs,
                "doctor_utilization": doctor_utilization,
            },
            "lab_metrics": {
                "total_orders": total_lab_orders,
                "pending_orders": pending_lab_orders,
                "released_reports": released_lab_reports,
            },
            "pharmacy_metrics": {
                "active_batches": active_batches,
                "low_stock_count": low_stock_count,
                "near_expiry_count": near_expiry_count,
                "expired_count": expired_count,
                "pharmacy_sales_total": float(pharmacy_sales_total),
            },
        }


admin_service = AdminService()
