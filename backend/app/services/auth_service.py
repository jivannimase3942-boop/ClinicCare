import random
import smtplib
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, Patient, Doctor, Department, EmailVerification
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    PatientProfileResponse,
    DoctorProfileResponse,
    DoctorAccessRequest,
    FrontDeskAccessRequest,
)


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

        # 4. Generate 6-digit numeric OTP and securely hash it
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

                text_content = (
                    f"Hello {full_name or 'Patient'},\n\n"
                    f"Your ClinicCare 6-digit verification code is: {otp_code}\n"
                    f"This code will expire in 10 minutes.\n\n"
                    f"If you did not request this verification, please disregard this message.\n\n"
                    f"Thank you,\nClinicCare Multispeciality Healthcare"
                )
                msg.attach(MIMEText(text_content, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                email_sent = True
            except Exception as e:
                # Log without exposing the OTP
                print(f"[ClinicCare] SMTP send notice for {normalized_email}: {e}")

        result: Dict[str, Any] = {
            "email": normalized_email,
            "message": f"Verification code sent to {normalized_email}",
            "expires_in_minutes": 10,
        }
        # In non-production development environments where SMTP is unconfigured, provide dev code for testing
        if settings.ENVIRONMENT != "production" and (settings.DEBUG or not settings.SMTP_HOST):
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
            # Check if recently verified already (within 15 min)
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

        # If OTP is provided, verify it and consume single-use status
        if reg_data.otp:
            AuthService.verify_registration_otp(db, normalized_email, reg_data.otp)
            # Invalidate all verification records for this email to prevent reuse
            db.query(EmailVerification).filter(EmailVerification.email == normalized_email).delete()
            db.commit()

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
    def request_doctor_access(db: Session, data: DoctorAccessRequest) -> User:
        normalized_email = data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError("Email is already registered")

        # Verify and consume OTP
        AuthService.verify_registration_otp(db, normalized_email, data.otp)
        db.query(EmailVerification).filter(EmailVerification.email == normalized_email).delete()
        db.commit()

        # Create doctor account in PENDING_DOCTOR status
        user = User(
            email=normalized_email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role="PENDING_DOCTOR",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Resolve department
        dept_id = data.department_id
        if not dept_id:
            dept = db.query(Department).first()
            if dept:
                dept_id = dept.id
            else:
                dept_id = "general"

        doc = Doctor(
            user_id=user.id,
            department_id=dept_id,
            specialization=data.specialization,
            qualification=data.qualification,
            experience_years=data.experience_years,
            is_active=False,  # inactive until approved by admin
        )
        db.add(doc)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def request_frontdesk_access(db: Session, data: FrontDeskAccessRequest) -> User:
        normalized_email = data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError("Email is already registered")

        # Verify and consume OTP
        AuthService.verify_registration_otp(db, normalized_email, data.otp)
        db.query(EmailVerification).filter(EmailVerification.email == normalized_email).delete()
        db.commit()

        # Create front desk account in PENDING_FRONT_DESK status
        user = User(
            email=normalized_email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role="PENDING_FRONT_DESK",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def send_login_otp(db: Session, email: str) -> Dict[str, Any]:
        normalized_email = email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user:
            raise ValueError("No account found with this email. Please register first.")
        if not user.is_active:
            raise ValueError("Account is disabled. Please contact administration.")

        now = datetime.now(timezone.utc)
        recent = db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.created_at >= now - timedelta(seconds=60)
        ).first()
        if recent:
            raise ValueError("Please wait 60 seconds before requesting another code.")

        db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.is_verified == False
        ).delete()

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

        email_sent = False
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Your ClinicCare Login Code: {otp_code}"
                msg["From"] = settings.SMTP_SENDER
                msg["To"] = normalized_email

                text_content = (
                    f"Hello {user.full_name},\n\n"
                    f"Your ClinicCare login code is: {otp_code}\n"
                    f"This code will expire in 10 minutes.\n\n"
                    f"ClinicCare Multispeciality Healthcare"
                )
                msg.attach(MIMEText(text_content, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                email_sent = True
            except Exception as e:
                print(f"[ClinicCare] SMTP send notice for {normalized_email}: {e}")

        result: Dict[str, Any] = {
            "email": normalized_email,
            "message": f"Login code sent to {normalized_email}",
            "expires_in_minutes": 10,
        }
        if settings.ENVIRONMENT != "production" and (settings.DEBUG or not settings.SMTP_HOST):
            result["dev_code"] = otp_code

        return result

    @staticmethod
    def verify_login_otp(db: Session, email: str, otp: str) -> User:
        normalized_email = email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user:
            raise ValueError("No account found with this email.")
        if not user.is_active:
            raise ValueError("Account is disabled.")

        AuthService.verify_registration_otp(db, normalized_email, otp)
        db.query(EmailVerification).filter(EmailVerification.email == normalized_email).delete()
        db.commit()
        return user

    @staticmethod
    def authenticate_google(db: Session, token: str, requested_role: str = "PATIENT") -> User:
        # Verify with Google OAuth2 tokeninfo endpoint
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(token)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ClinicCare-Auth/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise ValueError("Invalid Google authentication token")
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Google token verification failed: {str(e)}")

        email = data.get("email")
        if not email or data.get("email_verified") not in [True, "true", "True"]:
            raise ValueError("Google account does not have a verified email address")

        normalized_email = email.strip().lower()
        full_name = data.get("name") or "Google User"

        # Check if user already exists
        user = db.query(User).filter(User.email == normalized_email).first()
        if user:
            if not user.is_active:
                raise ValueError("User account is disabled")
            # Existing account resolves to their existing role (Google cannot escalate)
            return user

        # New user via Google:
        # Never allow Google to create ADMIN or elevate to DOCTOR/FRONT_DESK directly
        role_req = (requested_role or "PATIENT").upper()
        if role_req in ["ADMIN", "FRONT_DESK", "DOCTOR"]:
            # If requested a staff role via Google, set as pending approval
            if role_req == "DOCTOR":
                role_to_set = "PENDING_DOCTOR"
            elif role_req in ["FRONT_DESK", "ADMIN"]:
                role_to_set = "PENDING_FRONT_DESK"
            else:
                role_to_set = "PATIENT"
        else:
            role_to_set = "PATIENT"

        user = User(
            email=normalized_email,
            password_hash=get_password_hash(f"google_oauth_{random.randint(100000, 999999)}"),
            full_name=full_name,
            role=role_to_set,
            is_active=True,
        )
        db.add(user)
        db.flush()

        if user.role == "PATIENT":
            patient = Patient(user_id=user.id)
            db.add(patient)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def approve_pending_staff(db: Session, user_id: str, new_role: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        target_role = new_role.upper()
        if target_role not in ["DOCTOR", "FRONT_DESK", "PATIENT"]:
            raise ValueError(f"Invalid approval role: {target_role}")

        user.role = target_role
        user.is_active = True

        if target_role == "DOCTOR" and user.doctor_profile:
            user.doctor_profile.is_active = True

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
