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
            slot_duration_minutes=doc.slot_duration_minutes,
            profile_image=doc.profile_image,
            is_active=doc.is_active,
        )

    @staticmethod
    def get_or_generate_slots_for_date(db: Session, doctor_id: str, slot_date: date) -> List[DoctorSlotResponse]:
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        slots = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.slot_date == slot_date
        ).order_by(DoctorSlot.start_time.asc()).all()

        booked_times = set(
            a.appointment_time for a in db.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == slot_date,
                Appointment.status.in_(["confirmed", "pending"])
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
                
                curr_dt = datetime.combine(slot_date, time(start_h, start_m))
                end_dt = datetime.combine(slot_date, time(end_h, end_m))
                duration = timedelta(minutes=doc.slot_duration_minutes or 30)

                while curr_dt + duration <= end_dt:
                    start_str = curr_dt.strftime("%H:%M")
                    next_dt = curr_dt + duration
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


doctor_service = DoctorService()

