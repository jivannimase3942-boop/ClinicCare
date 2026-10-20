import secrets
import smtplib
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, validate_password_strength
from app.core.roles import get_permissions_for_role
from app.models.user import User, Patient, Doctor, Department, EmailVerification
from app.services.email_service import email_service
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
            EmailVerification.purpose == "registration",
            EmailVerification.created_at >= now - timedelta(seconds=60)
        ).first()
        if recent:
            raise ValueError("Please wait 60 seconds before requesting another verification code.")

        # 3. Invalidate previous pending registration OTPs for this email
        db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.purpose == "registration",
            EmailVerification.is_verified == False
        ).delete()

        # 4. Generate 6-digit numeric OTP using CSPRNG and securely hash it
        otp_code = f"{secrets.SystemRandom().randint(100000, 999999)}"
        otp_hash = get_password_hash(otp_code)
        expires_at = now + timedelta(minutes=10)

        ev = EmailVerification(
            email=normalized_email,
            otp_hash=otp_hash,
            attempts=0,
            max_attempts=5,
            is_verified=False,
            purpose="registration",
            expires_at=expires_at,
            created_at=now,
        )
        db.add(ev)
        db.commit()

        # 5. Dispatch email via email_service
        try:
            email_result = email_service.send_otp_email(
                to_email=normalized_email,
                otp_code=otp_code,
                full_name=full_name,
                purpose="account registration",
            )
        except Exception:
            db.delete(ev)
            db.commit()
            raise

        result: Dict[str, Any] = {
            "email": normalized_email,
            "message": f"Verification code sent to {normalized_email}",
            "expires_in_minutes": 10,
            "email_dispatched": email_result.get("dispatched", False),
            "email_configured": email_result.get("email_configured", False),
            "smtp_configured": email_result.get("smtp_configured", False),
            "provider": email_result.get("provider", "resend"),
        }
        # In non-production development environments where email is unconfigured or debug is active, provide dev code for testing
        if not settings.is_production and (settings.DEBUG or not email_service.is_configured()):
            result["dev_code"] = otp_code

        return result

    @staticmethod
    def verify_otp(db: Session, email: str, otp: str, purpose: str = "registration") -> bool:
        normalized_email = email.strip().lower()
        ev = db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.purpose == purpose,
            EmailVerification.is_verified == False
        ).order_by(EmailVerification.created_at.desc()).first()

        if not ev:
            # Check if recently verified already (within 15 min) for registration
            if purpose == "registration":
                already_verified = db.query(EmailVerification).filter(
                    EmailVerification.email == normalized_email,
                    EmailVerification.purpose == purpose,
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

        if not verify_password(otp.strip(), ev.otp_hash):
            ev.attempts += 1
            db.commit()
            remaining = max(0, ev.max_attempts - ev.attempts)
            raise ValueError(f"Invalid verification code. {remaining} attempt(s) remaining.")

        ev.attempts += 1
        ev.is_verified = True
        db.commit()
        return True

    @staticmethod
    def verify_registration_otp(db: Session, email: str, otp: str) -> bool:
        return AuthService.verify_otp(db, email=email, otp=otp, purpose="registration")

    @staticmethod
    def register_user(db: Session, reg_data: UserRegister) -> User:
        # Check existing email
        normalized_email = reg_data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError("Email is already registered")

        # Role restrictions: prevent public registration of privileged accounts
        requested_role = (reg_data.role or "PATIENT").upper()
        if requested_role in ["ADMIN", "FRONT_DESK", "BRANCH_ADMIN", "ORGANIZATION_ADMIN", "SUPER_ADMIN"]:
            raise ValueError("Administrative and privileged roles cannot be registered through public registration")
        if requested_role == "DOCTOR":
            raise ValueError("Doctor accounts require clinical verification and administrator provisioning")
        if requested_role != "PATIENT":
            raise ValueError("Privileged and staff roles cannot be registered through public registration")

        # Validate password strength
        valid, err_msg = validate_password_strength(reg_data.password)
        if not valid:
            raise ValueError(err_msg or "Password does not meet security requirements")

        # If OTP is provided, verify it and consume single-use status
        if reg_data.otp:
            AuthService.verify_registration_otp(db, normalized_email, reg_data.otp)
            db.query(EmailVerification).filter(
                EmailVerification.email == normalized_email,
                EmailVerification.purpose == "registration"
            ).delete()
            db.commit()
        else:
            if settings.is_production:
                verified_ev = db.query(EmailVerification).filter(
                    EmailVerification.email == normalized_email,
                    EmailVerification.purpose == "registration",
                    EmailVerification.is_verified == True,
                    EmailVerification.created_at >= datetime.now(timezone.utc) - timedelta(minutes=15)
                ).first()
                if not verified_ev:
                    raise ValueError("Email verification code is required to complete registration")
                db.query(EmailVerification).filter(
                    EmailVerification.email == normalized_email,
                    EmailVerification.purpose == "registration"
                ).delete()
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
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise ValueError("Email is already registered")

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

        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise ValueError("Email is already registered")

        return user

    @staticmethod
    def request_doctor_access(db: Session, data: DoctorAccessRequest) -> User:
        normalized_email = data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError("Email is already registered")

        valid, err_msg = validate_password_strength(data.password)
        if not valid:
            raise ValueError(err_msg or "Password does not meet security requirements")

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

        valid, err_msg = validate_password_strength(data.password)
        if not valid:
            raise ValueError(err_msg or "Password does not meet security requirements")

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
        if not user or not user.is_active:
            # Defensive response to prevent account enumeration / harvesting
            return {
                "email": normalized_email,
                "message": f"If an active account is registered with {normalized_email}, a verification code has been dispatched.",
                "expires_in_minutes": 10,
                "email_dispatched": True,
                "email_configured": email_service.is_configured(),
                "smtp_configured": email_service.is_configured(),
                "provider": email_service.get_active_provider(),
            }

        now = datetime.now(timezone.utc)
        recent = db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.purpose == "login",
            EmailVerification.created_at >= now - timedelta(seconds=60)
        ).first()
        if recent:
            raise ValueError("Please wait 60 seconds before requesting another code.")

        db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.purpose == "login",
            EmailVerification.is_verified == False
        ).delete()

        otp_code = f"{secrets.SystemRandom().randint(100000, 999999)}"
        otp_hash = get_password_hash(otp_code)
        expires_at = now + timedelta(minutes=10)

        ev = EmailVerification(
            email=normalized_email,
            otp_hash=otp_hash,
            attempts=0,
            max_attempts=5,
            is_verified=False,
            purpose="login",
            expires_at=expires_at,
            created_at=now,
        )
        db.add(ev)
        db.commit()

        # Dispatch email via email_service
        try:
            email_result = email_service.send_otp_email(
                to_email=normalized_email,
                otp_code=otp_code,
                full_name=user.full_name,
                purpose="portal login",
            )
        except Exception:
            db.delete(ev)
            db.commit()
            raise

        result: Dict[str, Any] = {
            "email": normalized_email,
            "message": f"Login code sent to {normalized_email}",
            "expires_in_minutes": 10,
            "email_dispatched": email_result.get("dispatched", False),
            "email_configured": email_result.get("email_configured", False),
            "smtp_configured": email_result.get("smtp_configured", False),
            "provider": email_result.get("provider", "resend"),
        }
        if not settings.is_production and (settings.DEBUG or not email_service.is_configured()):
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

        AuthService.verify_otp(db, normalized_email, otp, purpose="login")
        db.query(EmailVerification).filter(
            EmailVerification.email == normalized_email,
            EmailVerification.purpose == "login"
        ).delete()
        db.commit()
        return user

    @staticmethod
    def _fetch_google_token_info(token: str) -> Dict[str, Any]:
        """Fetches Google ID token details from official Google OAuth2 tokeninfo endpoint."""
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(token)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ClinicCare-Auth/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise ValueError("Invalid Google authentication token")
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def authenticate_google(db: Session, token: str, requested_role: str = "PATIENT") -> User:
        """
        Independently verifies Google ID token, validates signature, issuer, audience, and expiration.
        Creates patient account if new, or authenticates existing account preserving roles.
        Guarantees concurrency safety without duplicate account creation.
        """
        try:
            data = AuthService._fetch_google_token_info(token)
        except Exception as e:
            raise ValueError(f"Google token verification failed: {str(e)}")

        # 1. Validate issuer
        issuer = data.get("iss")
        if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid Google token issuer")

        # 2. Validate audience if GOOGLE_CLIENT_ID is configured
        if getattr(settings, "GOOGLE_CLIENT_ID", None) and str(settings.GOOGLE_CLIENT_ID).strip():
            token_aud = data.get("aud")
            if token_aud != str(settings.GOOGLE_CLIENT_ID).strip():
                raise ValueError("Google token audience does not match configured client ID")

        # 3. Validate expiration
        exp = data.get("exp")
        if exp is not None:
            try:
                exp_ts = float(exp)
            except (ValueError, TypeError):
                exp_ts = None
            if exp_ts is not None and time.time() > exp_ts:
                raise ValueError("Google authentication token has expired")

        # 4. Enforce verified email
        email = data.get("email")
        if not email or data.get("email_verified") not in [True, "true", "True"]:
            raise ValueError("Google account does not have a verified email address")

        normalized_email = email.strip().lower()
        full_name = data.get("name") or "Google User"

        # 5. Check if user already exists
        user = db.query(User).filter(User.email == normalized_email).first()
        if user:
            if not user.is_active:
                raise ValueError("User account is disabled")
            # Existing account resolves to their existing role (Google cannot escalate)
            return user

        # 6. New user via Google: role is strictly PATIENT (never elevate to ADMIN/DOCTOR)
        role_to_set = "PATIENT"

        try:
            user = User(
                email=normalized_email,
                password_hash=get_password_hash(f"google_oauth_{secrets.token_urlsafe(32)}"),
                full_name=full_name,
                role=role_to_set,
                is_active=True,
            )
            db.add(user)
            db.flush()

            patient = Patient(user_id=user.id)
            db.add(patient)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            # Handle concurrent race condition: user was created concurrently
            user = db.query(User).filter(User.email == normalized_email).first()
            if user:
                if not user.is_active:
                    raise ValueError("User account is disabled")
                return user
            raise ValueError("Failed to complete Google authentication due to concurrent conflict")

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
    def create_token_for_user(
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> str:
        import uuid
        token_jti = str(uuid.uuid4())
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "jti": token_jti,
        }
        token = create_access_token(token_data)

        # Track active session in database
        try:
            from app.models.security_privacy import UserSession
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            new_session = UserSession(
                user_id=user.id,
                token_jti=token_jti,
                ip_address=ip_address,
                user_agent=user_agent[:255] if user_agent else None,
                is_active=True,
                last_activity_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            if db is not None:
                db.add(new_session)
                db.commit()
            else:
                from app.db.session import SessionLocal
                with SessionLocal() as session_db:
                    session_db.add(new_session)
                    session_db.commit()
        except Exception as e:
            print(f"[AuthService] Note tracking user session: {e}")

        return token

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

        clinic_name = user.clinic.name if user.clinic else None
        perms = get_permissions_for_role(user.role)

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            patient_profile=patient_resp,
            doctor_profile=doctor_resp,
            clinic_id=user.clinic_id,
            clinic_name=clinic_name,
            permissions=perms,
        )


auth_service = AuthService()
