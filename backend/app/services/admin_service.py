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


admin_service = AdminService()
