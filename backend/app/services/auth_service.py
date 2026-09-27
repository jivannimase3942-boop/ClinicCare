from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, Patient, Doctor
from app.schemas.auth import UserRegister, UserLogin, UserResponse, PatientProfileResponse, DoctorProfileResponse


class AuthService:
    @staticmethod
    def register_user(db: Session, reg_data: UserRegister) -> User:
        # Check existing email
        existing = db.query(User).filter(User.email == reg_data.email.lower()).first()
        if existing:
            raise ValueError("Email is already registered")

        user = User(
            email=reg_data.email.lower(),
            password_hash=get_password_hash(reg_data.password),
            full_name=reg_data.full_name,
            phone=reg_data.phone,
            role=reg_data.role.upper() if reg_data.role else "PATIENT",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # If role is PATIENT, create Patient profile
        if user.role == "PATIENT":
            patient = Patient(
                user_id=user.id,
                date_of_birth=reg_data.date_of_birth,
                gender=reg_data.gender,
                blood_group=reg_data.blood_group,
                address=reg_data.address,
                emergency_contact=reg_data.emergency_contact,
            )
            db.add(patient)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Optional[User]:
        user = db.query(User).filter(User.email == login_data.email.lower()).first()
        if not user:
            return None
        if not verify_password(login_data.password, user.password_hash):
            return None
        if not user.is_active:
            raise ValueError("User account is disabled")
        return user

    @staticmethod
    def create_token_for_user(user: User) -> str:
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
        return create_access_token(token_data)

    @staticmethod
    def format_user_response(db: Session, user: User) -> UserResponse:
        patient_resp = None
        doctor_resp = None

        if user.patient_profile:
            patient_resp = PatientProfileResponse.model_validate(user.patient_profile)

        if user.doctor_profile:
            doc = user.doctor_profile
            dept_name = doc.department.name if doc.department else None
            doctor_resp = DoctorProfileResponse(
                id=doc.id,
                department_id=doc.department_id,
                department_name=dept_name,
                specialization=doc.specialization,
                qualification=doc.qualification,
                experience_years=doc.experience_years,
                consultation_fee=float(doc.consultation_fee),
                location=doc.location,
                available_days=doc.available_days,
                available_hours_start=doc.available_hours_start,
                available_hours_end=doc.available_hours_end,
                profile_image=doc.profile_image,
            )

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            patient_profile=patient_resp,
            doctor_profile=doctor_resp,
        )


auth_service = AuthService()
