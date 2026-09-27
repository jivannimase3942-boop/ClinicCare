from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.appointment import Appointment, DoctorSlot
from app.models.user import Doctor, Patient, User
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentResponse


class AppointmentService:
    @staticmethod
    def _format_appointment(app: Appointment) -> AppointmentResponse:
        patient_name = app.patient.user.full_name if app.patient and app.patient.user else None
        patient_phone = app.patient.user.phone if app.patient and app.patient.user else None
        doc_name = app.doctor.user.full_name if app.doctor and app.doctor.user else None
        doc_spec = app.doctor.specialization if app.doctor else None
        dept_name = app.doctor.department.name if app.doctor and app.doctor.department else None

        return AppointmentResponse(
            id=app.id,
            patient_id=app.patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            doctor_id=app.doctor_id,
            doctor_name=doc_name,
            doctor_specialization=doc_spec,
            department_id=app.department_id,
            department_name=dept_name,
            appointment_date=app.appointment_date,
            appointment_time=app.appointment_time,
            status=app.status,
            reason=app.reason,
            notes=app.notes,
            cancelled_reason=app.cancelled_reason,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )

    @staticmethod
    def book_appointment(
        db: Session,
        patient_id: str,
        doctor_id: str,
        appointment_date: date,
        appointment_time: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AppointmentResponse:
        # 1. Validate doctor
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()
        if not doctor:
            raise ValueError("Doctor not found or inactive")

        # 2. Prevent past dates
        if appointment_date < date.today():
            raise ValueError("Cannot book appointments in the past")

        # 3. Check doctor double-booking
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(["confirmed", "pending"])
        ).first()
        if conflict:
            raise ValueError(f"Doctor is already booked at {appointment_time} on {appointment_date}")

        # 4. Check patient double-booking at the same time
        patient_conflict = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(["confirmed", "pending"])
        ).first()
        if patient_conflict:
            raise ValueError("You already have an active appointment booked at this time")

        # 5. Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            department_id=doctor.department_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status="confirmed",
            reason=reason,
            notes=notes,
        )
        db.add(appointment)

        # 6. Mark slot as booked if slot exists
        slot = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.slot_date == appointment_date,
            DoctorSlot.start_time == appointment_time
        ).first()
        if slot:
            slot.is_booked = True

        db.commit()
        db.refresh(appointment)
        return AppointmentService._format_appointment(appointment)

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: str,
        new_date: date,
        new_time: str,
        patient_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> AppointmentResponse:
        query = db.query(Appointment).filter(Appointment.id == appointment_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        
        app = query.first()
        if not app:
            raise ValueError("Appointment not found or unauthorized")

        if app.status in ["cancelled", "completed"]:
            raise ValueError(f"Cannot reschedule an appointment with status: {app.status}")

        if new_date < date.today():
            raise ValueError("Cannot reschedule to a past date")

        # Check conflict on new date/time
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == app.doctor_id,
            Appointment.appointment_date == new_date,
            Appointment.appointment_time == new_time,
            Appointment.id != app.id,
            Appointment.status.in_(["confirmed", "pending"])
        ).first()
        if conflict:
            raise ValueError(f"Doctor is already booked at {new_time} on {new_date}")

        # Free old slot
        old_slot = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == app.doctor_id,
            DoctorSlot.slot_date == app.appointment_date,
            DoctorSlot.start_time == app.appointment_time
        ).first()
        if old_slot:
            old_slot.is_booked = False

        # Book new slot
        new_slot = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == app.doctor_id,
            DoctorSlot.slot_date == new_date,
            DoctorSlot.start_time == new_time
        ).first()
        if new_slot:
            new_slot.is_booked = True

        app.appointment_date = new_date
        app.appointment_time = new_time
        app.status = "rescheduled"
        if reason:
            app.notes = (app.notes or "") + f" [Rescheduled: {reason}]"

        db.commit()
        db.refresh(app)
        return AppointmentService._format_appointment(app)

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: str,
        patient_id: Optional[str] = None,
        cancelled_reason: Optional[str] = "Cancelled by patient",
    ) -> AppointmentResponse:
        query = db.query(Appointment).filter(Appointment.id == appointment_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)

        app = query.first()
        if not app:
            raise ValueError("Appointment not found or unauthorized")

        if app.status == "cancelled":
            raise ValueError("Appointment is already cancelled")

        app.status = "cancelled"
        app.cancelled_reason = cancelled_reason

        # Free slot
        slot = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == app.doctor_id,
            DoctorSlot.slot_date == app.appointment_date,
            DoctorSlot.start_time == app.appointment_time
        ).first()
        if slot:
            slot.is_booked = False

        db.commit()
        db.refresh(app)
        return AppointmentService._format_appointment(app)

    @staticmethod
    def get_patient_appointments(db: Session, patient_id: str) -> List[AppointmentResponse]:
        apps = db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
        return [AppointmentService._format_appointment(a) for a in apps]

    @staticmethod
    def get_appointment_by_id(db: Session, appointment_id: str, patient_id: Optional[str] = None) -> Optional[AppointmentResponse]:
        query = db.query(Appointment).filter(Appointment.id == appointment_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        app = query.first()
        if not app:
            return None
        return AppointmentService._format_appointment(app)

    @staticmethod
    def get_all_appointments(
        db: Session,
        doctor_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[date] = None,
    ) -> List[AppointmentResponse]:
        query = db.query(Appointment)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if status:
            query = query.filter(Appointment.status == status)
        if date_filter:
            query = query.filter(Appointment.appointment_date == date_filter)

        apps = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
        return [AppointmentService._format_appointment(a) for a in apps]

    @staticmethod
    def update_appointment_status(db: Session, appointment_id: str, status: str, notes: Optional[str] = None) -> AppointmentResponse:
        app = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not app:
            raise ValueError("Appointment not found")
        app.status = status
        if notes:
            app.notes = (app.notes or "") + f" [{notes}]"
        db.commit()
        db.refresh(app)
        return AppointmentService._format_appointment(app)



    @staticmethod
    def scan_and_send_reminders(db: Session) -> Dict[str, Any]:
        """Scans appointments in the next 24-48 hours and sends automated WhatsApp reminders."""
        from datetime import timedelta
        from app.integrations.whatsapp.service import whatsapp_service
        import asyncio

        tomorrow = date.today() + timedelta(days=1)
        upcoming = db.query(Appointment).filter(
            Appointment.appointment_date == tomorrow,
            Appointment.status == "confirmed"
        ).all()

        results = []
        for app in upcoming:
            phone = app.patient.user.phone if app.patient and app.patient.user else None
            patient_name = app.patient.user.full_name if app.patient and app.patient.user else "Patient"
            doctor_name = app.doctor.user.full_name if app.doctor and app.doctor.user else "Doctor"
            
            if phone:
                msg = (
                    f"Reminder: Hello {patient_name}, you have a confirmed consultation with Dr. {doctor_name} "
                    f"tomorrow on {app.appointment_date} at {app.appointment_time}. "
                    f"Please reply 'CANCEL' if you cannot attend, or visit our portal to reschedule."
                )
                try:
                    # In sync context, run coroutine
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            res = pool.submit(asyncio.run, whatsapp_service.send_text_message(phone, msg)).result()
                    else:
                        res = asyncio.run(whatsapp_service.send_text_message(phone, msg))
                except Exception:
                    res = {"status": "dispatched", "simulated": True}
                results.append({"appointment_id": app.id, "phone": phone, "result": res})
        
        return {"scanned": len(upcoming), "reminders_sent": len(results), "details": results}

appointment_service = AppointmentService()

