from datetime import date, datetime, time, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, Doctor, Department
from app.models.appointment import DoctorSlot, Appointment
from app.schemas.doctor import DoctorResponse, DepartmentResponse, DoctorSlotResponse


class DoctorService:
    @staticmethod
    def get_departments(db: Session, active_only: bool = True) -> List[DepartmentResponse]:
        query = db.query(Department)
        if active_only:
            query = query.filter(Department.is_active == True)
        depts = query.order_by(Department.name.asc()).all()
        return [DepartmentResponse.model_validate(d) for d in depts]

    @staticmethod
    def get_department_by_id(db: Session, dept_id: str) -> Optional[Department]:
        return db.query(Department).filter(Department.id == dept_id).first()

    @staticmethod
    def create_department(db: Session, name: str, description: Optional[str] = None, icon: str = "Activity") -> Department:
        dept = Department(name=name, description=description, icon=icon, is_active=True)
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def get_doctors(
        db: Session,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[DoctorResponse]:
        query = db.query(Doctor).join(User, Doctor.user_id == User.id).join(Department, Doctor.department_id == Department.id)
        
        if active_only:
            query = query.filter(Doctor.is_active == True, User.is_active == True)

        if department_id:
            query = query.filter(Doctor.department_id == department_id)

        if search:
            search_fmt = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_fmt),
                    Doctor.specialization.ilike(search_fmt),
                    Doctor.qualification.ilike(search_fmt),
                    Department.name.ilike(search_fmt),
                )
            )

        doctors = query.all()
        return [DoctorService.get_doctor_by_id(db, doc.id) for doc in doctors]

    @staticmethod
    def get_doctor_by_id(db: Session, doctor_id: str) -> Optional[DoctorResponse]:
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            return None
        return DoctorResponse(
            id=doc.id,
            user_id=doc.user_id,
            full_name=doc.user.full_name,
            email=doc.user.email,
            phone=doc.user.phone,
            department_id=doc.department_id,
            department_name=doc.department.name if doc.department else None,
            specialization=doc.specialization,
            qualification=doc.qualification,
            experience_years=doc.experience_years,
            consultation_fee=float(doc.consultation_fee),
            location=doc.location,
            available_days=doc.available_days,
            available_hours_start=doc.available_hours_start,
            available_hours_end=doc.available_hours_end,
            break_start_time=getattr(doc, "break_start_time", "13:00") or "13:00",
            break_end_time=getattr(doc, "break_end_time", "14:00") or "14:00",
            max_daily_patients=getattr(doc, "max_daily_patients", 30) or 30,
            slot_duration_minutes=doc.slot_duration_minutes,
            profile_image=doc.profile_image,
            is_active=doc.is_active,
        )

    @staticmethod
    def get_or_generate_slots_for_date(db: Session, doctor_id: str, slot_date: date) -> List[DoctorSlotResponse]:
        from app.models.appointment import DoctorLeave
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        # 1. Check if doctor is on leave on this date
        leave = db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.start_date <= slot_date,
            DoctorLeave.end_date >= slot_date,
            DoctorLeave.is_approved == True
        ).first()
        if leave:
            return []

        slots = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.slot_date == slot_date
        ).order_by(DoctorSlot.start_time.asc()).all()

        booked_times = set(
            a.appointment_time for a in db.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == slot_date,
                Appointment.status.in_(["confirmed", "pending", "checked_in", "in_consultation"])
            ).all()
        )

        if slots:
            for slot in slots:
                if slot.start_time in booked_times and not slot.is_booked:
                    slot.is_booked = True
                elif slot.start_time not in booked_times and slot.is_booked:
                    slot.is_booked = False
            db.commit()
            return [DoctorSlotResponse.model_validate(s) for s in slots]

        day_name = slot_date.strftime("%A")
        available_days = [d.strip() for d in doc.available_days.split(",")]
        
        generated_slots = []
        if day_name in available_days:
            try:
                start_h, start_m = map(int, doc.available_hours_start.split(":"))
                end_h, end_m = map(int, doc.available_hours_end.split(":"))
                
                break_start = getattr(doc, "break_start_time", None) or "13:00"
                break_end = getattr(doc, "break_end_time", None) or "14:00"
                
                b_start_h, b_start_m = map(int, break_start.split(":"))
                b_end_h, b_end_m = map(int, break_end.split(":"))
                break_start_dt = datetime.combine(slot_date, time(b_start_h, b_start_m))
                break_end_dt = datetime.combine(slot_date, time(b_end_h, b_end_m))

                curr_dt = datetime.combine(slot_date, time(start_h, start_m))
                end_dt = datetime.combine(slot_date, time(end_h, end_m))
                duration = timedelta(minutes=doc.slot_duration_minutes or 30)

                while curr_dt + duration <= end_dt:
                    next_dt = curr_dt + duration
                    
                    # Check break overlap: if slot overlaps with break interval, skip it
                    if not (next_dt <= break_start_dt or curr_dt >= break_end_dt):
                        curr_dt = next_dt
                        continue

                    start_str = curr_dt.strftime("%H:%M")
                    end_str = next_dt.strftime("%H:%M")
                    is_booked = start_str in booked_times

                    slot = DoctorSlot(
                        doctor_id=doctor_id,
                        slot_date=slot_date,
                        start_time=start_str,
                        end_time=end_str,
                        is_booked=is_booked,
                    )
                    db.add(slot)
                    generated_slots.append(slot)
                    curr_dt = next_dt

                db.commit()
                for s in generated_slots:
                    db.refresh(s)
            except Exception as e:
                db.rollback()
                raise ValueError(f"Failed to generate slots: {str(e)}")

        return [DoctorSlotResponse.model_validate(s) for s in generated_slots]

    @staticmethod
    def add_doctor_leave(
        db: Session,
        doctor_id: str,
        start_date: date,
        end_date: date,
        reason: Optional[str] = None,
        clinic_id: Optional[str] = None,
    ):
        from app.models.appointment import DoctorLeave
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date")

        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        resolved_clinic = clinic_id or (doc.user.clinic_id if doc.user else None)
        leave = DoctorLeave(
            doctor_id=doctor_id,
            clinic_id=resolved_clinic,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            is_approved=True,
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return leave

    @staticmethod
    def get_doctor_leaves(db: Session, doctor_id: str, clinic_id: Optional[str] = None):
        from app.models.appointment import DoctorLeave
        query = db.query(DoctorLeave).filter(DoctorLeave.doctor_id == doctor_id)
        if clinic_id:
            query = query.filter(DoctorLeave.clinic_id == clinic_id)
        return query.order_by(DoctorLeave.start_date.desc()).all()

    @staticmethod
    def update_doctor_schedule(db: Session, doctor_id: str, update_data: dict) -> DoctorResponse:
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        for key, val in update_data.items():
            if val is not None and hasattr(doc, key):
                setattr(doc, key, val)

        db.commit()
        db.refresh(doc)
        return DoctorService.get_doctor_by_id(db, doc.id)


doctor_service = DoctorService()


