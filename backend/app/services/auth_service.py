import random
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, Patient, Doctor, EmailVerification
from app.schemas.auth import UserRegister, UserLogin, UserResponse, PatientProfileResponse, DoctorProfileResponse


class AuthService:
    @staticmethod
    def send_registration_otp(db: Session, email: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        normalized_email = email.strip().lower()

        # 1. Check if email is already registered and active
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing and existing.is_active:
            raise ValueError("Email is already registered. Please log in.")

        now = datetime.now(timezone.utc)

        # 2. Rate limit: check if an OTP was sent in the last 60 seconds
        recent = db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.created_at >= now - timedelta(seconds=60)
        ).first()
        if recent:
            raise ValueError("Please wait 60 seconds before requesting another verification code.")

        # 3. Invalidate previous pending OTPs for this email
        db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.is_verified == False
        ).delete()

        # 4. Generate 6-digit numeric OTP
        otp_code = f"{random.randint(100000, 999999)}"
        otp_hash = get_password_hash(otp_code)
        expires_at = now + timedelta(minutes=10)

        ev = EmailVerification(
            email=normalized_email,
            otp_hash=otp_hash,
            attempts=0,
            max_attempts=5,
            is_verified=False,
            expires_at=expires_at,
            created_at=now,
        )
        db.add(ev)
        db.commit()

        # 5. Dispatch email if SMTP is configured
        email_sent = False
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Your ClinicCare Verification Code: {otp_code}"
                msg["From"] = settings.SMTP_SENDER
                msg["To"] = normalized_email

                text_content = f"Hello {full_name or 'Patient'},\n\nYour ClinicCare verification code is: {otp_code}\nThis code will expire in 10 minutes.\n\nThank you,\nClinicCare Multispeciality Hospital"
                msg.attach(MIMEText(text_content, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                email_sent = True
            except Exception as e:
                print(f"[ClinicCare] SMTP send notice: {e}")

        result: Dict[str, Any] = {
            "email": normalized_email,
            "message": f"Verification code sent to {normalized_email}",
            "expires_in_minutes": 10,
        }
        # In test / dev environments when SMTP is unconfigured, provide dev code for testing
        if not email_sent and (settings.DEBUG or settings.ENVIRONMENT != "production" or not settings.SMTP_HOST):
            result["dev_code"] = otp_code

        return result

    @staticmethod
    def verify_registration_otp(db: Session, email: str, otp: str) -> bool:
        normalized_email = email.strip().lower()
        ev = db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.is_verified == False
        ).order_by(EmailVerification.created_at.desc()).first()

        if not ev:
            # Check if recently verified already
            already_verified = db.query(EmailVerification).filter(
                EmailVerification.email == normalized_email,
                EmailVerification.is_verified == True,
                EmailVerification.created_at >= datetime.now(timezone.utc) - timedelta(minutes=15)
            ).first()
            if already_verified:
                return True
            raise ValueError("No active verification code found for this email. Please request a new code.")

        now = datetime.now(timezone.utc)
        exp = ev.expires_at if ev.expires_at.tzinfo else ev.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            raise ValueError("Verification code has expired. Please request a new code.")

        if ev.attempts >= ev.max_attempts:
            raise ValueError("Maximum verification attempts exceeded. Please request a new code.")

        ev.attempts += 1
        db.commit()

        if not verify_password(otp.strip(), ev.otp_hash):
            remaining = max(0, ev.max_attempts - ev.attempts)
            raise ValueError(f"Invalid verification code. {remaining} attempt(s) remaining.")

        ev.is_verified = True
        db.commit()
        return True

    @staticmethod
    def register_user(db: Session, reg_data: UserRegister) -> User:
        # Check existing email
        normalized_email = reg_data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError("Email is already registered")

        # Role restrictions: prevent public registration of privileged accounts
        requested_role = (reg_data.role or "PATIENT").upper()
        if requested_role in ["ADMIN", "FRONT_DESK"]:
            raise ValueError("Administrative roles cannot be registered through public registration")
        if requested_role == "DOCTOR":
            raise ValueError("Doctor accounts require clinical verification and administrator provisioning")

        # If OTP is provided, verify it
        if reg_data.otp:
            AuthService.verify_registration_otp(db, normalized_email, reg_data.otp)

        user = User(
            email=normalized_email,
            password_hash=get_password_hash(reg_data.password),
            full_name=reg_data.full_name,
            phone=reg_data.phone,
            role=requested_role,
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
