import re
import random
import json
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.clinic import Clinic
from app.models.user import User, Doctor, Department
from app.schemas.clinic import ClinicOnboardRequest, ClinicUpdateRequest, ClinicOnboardResponse, ClinicResponse
from app.core.security import get_password_hash
from app.services.audit_service import audit_service


def generate_slug(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return cleaned or f"clinic-{random.randint(1000, 9999)}"


class ClinicService:
    @staticmethod
    def get_or_create_default_clinic(db: Session) -> Clinic:
        default_slug = "cliniccare-central"
        clinic = db.query(Clinic).filter(Clinic.slug == default_slug).first()
        if not clinic:
            clinic = Clinic(
                name="ClinicCare Multispeciality Hospital",
                slug=default_slug,
                phone="+91 80 2345 6789",
                email="contact@cliniccare.in",
                address="100 Healthcare Boulevard, Koramangala",
                city="Bengaluru",
                state="Karnataka",
                pincode="560034",
                country="India",
                operating_hours="08:00 AM - 08:00 PM (Monday - Saturday)",
                consultation_fee_default=Decimal("500.00"),
                is_active=True,
                settings_json=json.dumps({
                    "default_currency": "INR",
                    "currency_symbol": "₹",
                    "time_zone": "Asia/Kolkata",
                    "emergency_available": True,
                    "telemedicine_ready": True
                })
            )
            db.add(clinic)
            db.commit()
            db.refresh(clinic)
        return clinic

    @staticmethod
    def onboard_clinic(
        db: Session,
        data: ClinicOnboardRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ClinicOnboardResponse:
        # 1. Normalize and validate admin email
        admin_email = data.admin_email.strip().lower()
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            raise ValueError(f"An account with email '{admin_email}' already exists. Please choose a different administrative email.")

        # 2. Generate slug and ensure uniqueness
        slug = (data.slug or generate_slug(data.name)).strip().lower()
        if db.query(Clinic).filter(Clinic.slug == slug).first():
            slug = f"{slug}-{random.randint(100, 999)}"

        # 3. Create Clinic
        clinic = Clinic(
            name=data.name.strip(),
            slug=slug,
            phone=data.phone,
            email=str(data.email) if data.email else None,
            address=data.address,
            city=data.city or "Bengaluru",
            state=data.state or "Karnataka",
            pincode=data.pincode,
            country=data.country or "India",
            operating_hours=data.operating_hours or "09:00 AM - 08:00 PM (Monday - Saturday)",
            consultation_fee_default=Decimal(str(data.consultation_fee_default or 500.00)),
            is_active=True,
            settings_json=json.dumps({
                "default_currency": "INR",
                "currency_symbol": "₹",
                "time_zone": "Asia/Kolkata",
                "departments": data.departments or ["General Medicine", "Pediatrics", "Cardiology"],
                "services": data.services or [],
                "onboarded_at": datetime_now_iso(),
            })
        )
        db.add(clinic)
        db.flush()

        # 4. Create primary Administrator User
        admin_user = User(
            email=admin_email,
            password_hash=get_password_hash(data.admin_password),
            full_name=data.admin_name.strip(),
            phone=data.admin_phone,
            role="ADMIN",
            clinic_id=clinic.id,
            is_active=True,
        )
        db.add(admin_user)
        db.flush()

        # 5. Create or link Clinic Departments
        dept_entities = []
        dept_names = data.departments or ["General Medicine", "Pediatrics", "Cardiology"]
        for d_name in dept_names:
            d_name_clean = d_name.strip()
            existing_dept = db.query(Department).filter(Department.name == d_name_clean).first()
            if existing_dept:
                dept_entities.append(existing_dept)
            else:
                dept = Department(
                    clinic_id=clinic.id,
                    name=d_name_clean,
                    description=f"{d_name_clean} Department at {clinic.name}",
                    icon="Activity",
                    is_active=True,
                )
                db.add(dept)
                dept_entities.append(dept)
        db.flush()

        # 6. Optional primary Doctor creation
        doc_user_info = None
        if data.doctor_name and data.doctor_email:
            doc_email = data.doctor_email.strip().lower()
            if not db.query(User).filter(User.email == doc_email).first():
                doc_user = User(
                    email=doc_email,
                    password_hash=get_password_hash("Doctor@123"),
                    full_name=data.doctor_name.strip(),
                    role="DOCTOR",
                    clinic_id=clinic.id,
                    is_active=True,
                )
                db.add(doc_user)
                db.flush()

                primary_dept = dept_entities[0] if dept_entities else None
                if primary_dept:
                    doc_profile = Doctor(
                        user_id=doc_user.id,
                        department_id=primary_dept.id,
                        specialization=data.doctor_specialization or "General Physician",
                        qualification=data.doctor_qualification or "MBBS, MD",
                        experience_years=5,
                        consultation_fee=Decimal(str(data.doctor_fee or clinic.consultation_fee_default)),
                        location=f"{clinic.name}, Room 101",
                        available_days="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
                        available_hours_start="09:00",
                        available_hours_end="18:00",
                        is_active=True,
                    )
                    db.add(doc_profile)
                    db.flush()
                    doc_user_info = {
                        "id": doc_user.id,
                        "email": doc_user.email,
                        "full_name": doc_user.full_name,
                        "role": doc_user.role,
                        "specialization": doc_profile.specialization,
                    }

        # 7. Record security audit log
        audit_service.log_action(
            db=db,
            action="CLINIC_ONBOARDED",
            user=admin_user,
            clinic_id=clinic.id,
            entity_type="Clinic",
            entity_id=clinic.id,
            details={
                "clinic_name": clinic.name,
                "slug": clinic.slug,
                "admin_email": admin_user.email,
                "departments": dept_names,
            },
            ip_address=client_ip,
            user_agent=user_agent,
        )

        db.commit()
        db.refresh(clinic)

        clinic_resp = ClinicResponse(
            id=clinic.id,
            name=clinic.name,
            slug=clinic.slug,
            phone=clinic.phone,
            email=clinic.email,
            address=clinic.address,
            city=clinic.city,
            state=clinic.state,
            pincode=clinic.pincode,
            country=clinic.country,
            operating_hours=clinic.operating_hours,
            consultation_fee_default=float(clinic.consultation_fee_default),
            is_active=clinic.is_active,
            settings_json=clinic.settings_json,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at,
        )

        return ClinicOnboardResponse(
            clinic=clinic_resp,
            admin_user={
                "id": admin_user.id,
                "email": admin_user.email,
                "full_name": admin_user.full_name,
                "role": admin_user.role,
                "clinic_id": clinic.id,
            },
            doctor_user=doc_user_info,
            portal_url=f"/clinic/{clinic.slug}",
            message=f"Clinic '{clinic.name}' successfully onboarded to ClinicCare SaaS platform.",
        )

    @staticmethod
    def get_clinic_by_id(db: Session, clinic_id: str) -> Optional[Clinic]:
        return db.query(Clinic).filter(Clinic.id == clinic_id).first()

    @staticmethod
    def get_clinic_by_slug(db: Session, slug: str) -> Optional[Clinic]:
        return db.query(Clinic).filter(Clinic.slug == slug.strip().lower()).first()

    @staticmethod
    def list_clinics(db: Session, active_only: bool = True) -> List[Clinic]:
        q = db.query(Clinic)
        if active_only:
            q = q.filter(Clinic.is_active == True)
        return q.order_by(Clinic.name.asc()).all()

    @staticmethod
    def update_clinic(
        db: Session,
        clinic_id: str,
        data: ClinicUpdateRequest,
        current_user: Optional[User] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Clinic:
        clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if not clinic:
            raise ValueError("Clinic not found")

        updates = {}
        for field in [
            "name", "phone", "email", "address", "city", "state", "pincode",
            "operating_hours", "consultation_fee_default", "settings_json"
        ]:
            val = getattr(data, field, None)
            if val is not None:
                if field == "consultation_fee_default":
                    setattr(clinic, field, Decimal(str(val)))
                elif field == "email":
                    setattr(clinic, field, str(val))
                else:
                    setattr(clinic, field, val)
                updates[field] = str(val)

        if updates:
            audit_service.log_action(
                db=db,
                action="CLINIC_PROFILE_UPDATED",
                user=current_user,
                clinic_id=clinic.id,
                entity_type="Clinic",
                entity_id=clinic.id,
                details=updates,
                ip_address=client_ip,
                user_agent=user_agent,
            )

        db.commit()
        db.refresh(clinic)
        return clinic


def datetime_now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


clinic_service = ClinicService()
