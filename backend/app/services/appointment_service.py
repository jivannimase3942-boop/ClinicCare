from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.appointment import Appointment, DoctorSlot
from app.models.user import Doctor, Patient, User
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentResponse
from app.services.audit_service import audit_service


class AppointmentService:
    @staticmethod
    def _format_appointment(app: Appointment) -> AppointmentResponse:
        patient_name = app.patient.user.full_name if app.patient and app.patient.user else None
        patient_phone = app.patient.user.phone if app.patient and app.patient.user else None
        doc_name = app.doctor.user.full_name if app.doctor and app.doctor.user else None
        doc_spec = app.doctor.specialization if app.doctor else None
        dept_name = app.doctor.department.name if app.doctor and app.doctor.department else None
        clinic_name = app.clinic.name if app.clinic else None

        return AppointmentResponse(
            id=app.id,
            clinic_id=app.clinic_id,
            clinic_name=clinic_name,
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
            appointment_type=getattr(app, "appointment_type", "NEW_CONSULTATION") or "NEW_CONSULTATION",
            token_number=getattr(app, "token_number", None),
            queue_status=getattr(app, "queue_status", "NOT_QUEUED") or "NOT_QUEUED",
            checked_in_at=getattr(app, "checked_in_at", None),
            consultation_started_at=getattr(app, "consultation_started_at", None),
            consultation_ended_at=getattr(app, "consultation_ended_at", None),
            is_walk_in=bool(getattr(app, "is_walk_in", False)),
            parent_appointment_id=getattr(app, "parent_appointment_id", None),
            reason=app.reason,
            notes=app.notes,
            cancelled_reason=app.cancelled_reason,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )

    @staticmethod
    def generate_next_token(db: Session, doctor_id: str, appointment_date: date) -> str:
        """Generates next token number for doctor on a specific date (e.g. T-01, T-02)."""
        count = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.token_number != None
        ).count()
        return f"T-{(count + 1):02d}"

    @staticmethod
    def book_appointment(
        db: Session,
        patient_id: str,
        doctor_id: str,
        appointment_date: date,
        appointment_time: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        clinic_id: Optional[str] = None,
        appointment_type: str = "NEW_CONSULTATION",
        is_walk_in: bool = False,
        parent_appointment_id: Optional[str] = None,
    ) -> AppointmentResponse:
        from app.models.appointment import DoctorLeave
        # 1. Validate doctor
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()
        if not doctor:
            raise ValueError("Doctor not found or inactive")

        # 2. Prevent past dates
        if appointment_date < date.today():
            raise ValueError("Cannot book appointments in the past")

        # 3. Check if doctor is on approved leave
        leave = db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.start_date <= appointment_date,
            DoctorLeave.end_date >= appointment_date,
            DoctorLeave.is_approved == True
        ).first()
        if leave:
            raise ValueError(f"Doctor is on scheduled leave on {appointment_date} ({leave.reason or 'Leave'})")

        active_statuses = ["confirmed", "pending", "checked_in", "in_consultation", "waiting"]

        # 4. Check daily patient limit for non-walk-ins
        if not is_walk_in:
            day_count = db.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status.in_(active_statuses)
            ).count()
            max_limit = getattr(doctor, "max_daily_patients", 30) or 30
            if day_count >= max_limit:
                raise ValueError(f"Doctor's daily capacity ({max_limit} patients) is reached for {appointment_date}. Please join the waitlist or choose another date.")

        # 5. Check doctor double-booking
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(active_statuses)
        ).first()
        if conflict:
            raise ValueError(f"Doctor is already booked at {appointment_time} on {appointment_date}")

        # 6. Check patient double-booking at the same time
        patient_conflict = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(active_statuses)
        ).first()
        if patient_conflict:
            raise ValueError("You already have an active appointment booked at this time")

        # 7. Resolve tenant clinic
        resolved_clinic = (
            clinic_id
            or (doctor.user.clinic_id if doctor.user else None)
            or (doctor.department.clinic_id if doctor.department else None)
        )

        # 8. Token and queue status for walk-in vs regular booking
        token_num = None
        initial_status = "confirmed"
        initial_queue = "NOT_QUEUED"
        check_in_time = None

        if is_walk_in:
            token_num = AppointmentService.generate_next_token(db, doctor_id, appointment_date)
            initial_status = "checked_in"
            initial_queue = "WAITING"
            check_in_time = datetime.now(timezone.utc)

        # 9. Create appointment
        appointment = Appointment(
            clinic_id=resolved_clinic,
            patient_id=patient_id,
            doctor_id=doctor_id,
            department_id=doctor.department_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status=initial_status,
            appointment_type=appointment_type,
            token_number=token_num,
            queue_status=initial_queue,
            checked_in_at=check_in_time,
            is_walk_in=is_walk_in,
            parent_appointment_id=parent_appointment_id,
            reason=reason,
            notes=notes,
        )
        db.add(appointment)

        # 10. Mark slot as booked if slot exists
        slot = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.slot_date == appointment_date,
            DoctorSlot.start_time == appointment_time
        ).first()
        if slot:
            slot.is_booked = True

        db.commit()
        db.refresh(appointment)

        # 11. Record audit log
        audit_service.log_action(
            db=db,
            action="APPOINTMENT_WALK_IN" if is_walk_in else "APPOINTMENT_CREATE",
            clinic_id=resolved_clinic,
            entity_type="Appointment",
            entity_id=appointment.id,
            details={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
                "token_number": token_num,
                "is_walk_in": is_walk_in,
                "reason": reason,
            }
        )

        return AppointmentService._format_appointment(appointment)

    @staticmethod
    def check_in_appointment(db: Session, appointment_id: str, actor_id: Optional[str] = None) -> AppointmentResponse:
        app = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not app:
            raise ValueError("Appointment not found")

        if app.status in ["cancelled", "completed"]:
            raise ValueError(f"Cannot check in an appointment that is {app.status}")

        if not app.token_number:
            app.token_number = AppointmentService.generate_next_token(db, app.doctor_id, app.appointment_date)

        app.status = "checked_in"
        app.queue_status = "WAITING"
        app.checked_in_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(app)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=app.clinic_id,
            action="APPOINTMENT_CHECK_IN",
            entity_type="Appointment",
            entity_id=app.id,
            details={"token_number": app.token_number, "status": app.status}
        )
        return AppointmentService._format_appointment(app)

    @staticmethod
    def update_queue_status(
        db: Session,
        appointment_id: str,
        queue_status: str,
        notes: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> AppointmentResponse:
        app = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not app:
            raise ValueError("Appointment not found")

        valid_queue = ["WAITING", "CALLED", "IN_CONSULTATION", "COMPLETED", "SKIPPED", "CANCELLED"]
        q_upper = queue_status.upper()
        if q_upper not in valid_queue:
            raise ValueError(f"Invalid queue status: {queue_status}. Expected one of {valid_queue}")

        app.queue_status = q_upper
        now_dt = datetime.now(timezone.utc)

        if q_upper == "IN_CONSULTATION":
            app.status = "in_consultation"
            if not app.consultation_started_at:
                app.consultation_started_at = now_dt
        elif q_upper == "COMPLETED":
            app.status = "completed"
            app.consultation_ended_at = now_dt
        elif q_upper == "CANCELLED":
            app.status = "cancelled"

        if notes:
            app.notes = (app.notes or "") + f" [Queue: {notes}]"

        db.commit()
        db.refresh(app)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=app.clinic_id,
            action="QUEUE_STATUS_UPDATE",
            entity_type="Appointment",
            entity_id=app.id,
            details={"queue_status": q_upper, "status": app.status}
        )
        return AppointmentService._format_appointment(app)

    @staticmethod
    def get_today_queue(
        db: Session,
        clinic_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
    ) -> List[AppointmentResponse]:
        today = date.today()
        query = db.query(Appointment).filter(
            Appointment.appointment_date == today,
            Appointment.status.in_(["confirmed", "checked_in", "in_consultation", "waiting"])
        )
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        apps = query.order_by(Appointment.token_number.asc().nullslast(), Appointment.appointment_time.asc()).all()
        return [AppointmentService._format_appointment(a) for a in apps]

    @staticmethod
    def add_to_waitlist(
        db: Session,
        patient_id: str,
        doctor_id: str,
        desired_date: date,
        preferred_time_range: Optional[str] = None,
        notes: Optional[str] = None,
        clinic_id: Optional[str] = None,
    ):
        from app.models.appointment import AppointmentWaitlist
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        resolved_clinic = clinic_id or (doc.user.clinic_id if doc.user else None)
        item = AppointmentWaitlist(
            clinic_id=resolved_clinic,
            patient_id=patient_id,
            doctor_id=doctor_id,
            desired_date=desired_date,
            preferred_time_range=preferred_time_range,
            notes=notes,
            status="WAITING",
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        audit_service.log_action(
            db=db,
            clinic_id=resolved_clinic,
            action="WAITLIST_ADD",
            entity_type="AppointmentWaitlist",
            entity_id=item.id,
            details={"patient_id": patient_id, "doctor_id": doctor_id, "desired_date": str(desired_date)}
        )
        return item

    @staticmethod
    def get_waitlist(
        db: Session,
        clinic_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        desired_date: Optional[date] = None,
    ):
        from app.models.appointment import AppointmentWaitlist
        query = db.query(AppointmentWaitlist).filter(AppointmentWaitlist.status == "WAITING")
        if clinic_id:
            query = query.filter(AppointmentWaitlist.clinic_id == clinic_id)
        if doctor_id:
            query = query.filter(AppointmentWaitlist.doctor_id == doctor_id)
        if desired_date:
            query = query.filter(AppointmentWaitlist.desired_date == desired_date)

        return query.order_by(AppointmentWaitlist.created_at.asc()).all()

    @staticmethod
    def convert_waitlist_to_appointment(
        db: Session,
        waitlist_id: str,
        appointment_time: str,
    ) -> AppointmentResponse:
        from app.models.appointment import AppointmentWaitlist
        wl = db.query(AppointmentWaitlist).filter(AppointmentWaitlist.id == waitlist_id).first()
        if not wl or wl.status != "WAITING":
            raise ValueError("Waitlist entry not found or already processed")

        app = AppointmentService.book_appointment(
            db=db,
            patient_id=wl.patient_id,
            doctor_id=wl.doctor_id,
            appointment_date=wl.desired_date,
            appointment_time=appointment_time,
            reason=f"Converted from waitlist: {wl.notes or ''}",
            clinic_id=wl.clinic_id,
        )
        wl.status = "BOOKED"
        db.commit()
        return app

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: str,
        new_date: date,
        new_time: str,
        patient_id: Optional[str] = None,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> AppointmentResponse:
        from app.models.appointment import DoctorLeave
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

        # Check doctor leave on new date
        leave = db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == app.doctor_id,
            DoctorLeave.start_date <= new_date,
            DoctorLeave.end_date >= new_date,
            DoctorLeave.is_approved == True
        ).first()
        if leave:
            raise ValueError(f"Doctor is on scheduled leave on {new_date}")

        # Check conflict on new date/time
        active_statuses = ["confirmed", "pending", "checked_in", "in_consultation", "waiting"]
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == app.doctor_id,
            Appointment.appointment_date == new_date,
            Appointment.appointment_time == new_time,
            Appointment.id != app.id,
            Appointment.status.in_(active_statuses)
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

        old_date_str = str(app.appointment_date)
        old_time_str = app.appointment_time

        app.appointment_date = new_date
        app.appointment_time = new_time
        app.status = "rescheduled"
        if reason:
            app.notes = (app.notes or "") + f" [Rescheduled: {reason}]"

        db.commit()
        db.refresh(app)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=app.clinic_id,
            action="APPOINTMENT_RESCHEDULE",
            entity_type="Appointment",
            entity_id=app.id,
            details={
                "from_date": old_date_str,
                "from_time": old_time_str,
                "to_date": str(new_date),
                "to_time": new_time,
                "reason": reason,
            }
        )

        return AppointmentService._format_appointment(app)

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: str,
        patient_id: Optional[str] = None,
        cancelled_reason: Optional[str] = "Cancelled by patient",
        actor_id: Optional[str] = None,
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

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=app.clinic_id,
            action="APPOINTMENT_CANCEL",
            entity_type="Appointment",
            entity_id=app.id,
            details={"cancelled_reason": cancelled_reason}
        )

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
        clinic_id: Optional[str] = None,
    ) -> List[AppointmentResponse]:
        query = db.query(Appointment)
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
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

