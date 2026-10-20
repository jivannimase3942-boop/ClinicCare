from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    SendOtpRequest,
    VerifyOtpRequest,
    DoctorAccessRequest,
    FrontDeskAccessRequest,
    GoogleAuthRequest,
    LoginSendOtpRequest,
    LoginVerifyOtpRequest,
)
from app.services.auth_service import auth_service
from app.services.security_privacy_service import SecurityPrivacyService
from app.services.email_service import (
    email_service,
    EmailNotConfiguredError,
    EmailConnectionError,
    EmailAuthenticationError,
    EmailDeliveryError,
    SMTPNotConfiguredError,
    SMTPConnectionError,
    SMTPAuthenticationError,
    SMTPDeliveryError,
    ResendNotConfiguredError,
    ResendConnectionError,
    ResendAuthenticationError,
    ResendRestrictedRecipientError,
    ResendValidationError,
    ResendRateLimitError,
    ResendDeliveryError,
    BrevoNotConfiguredError,
    BrevoConnectionError,
    BrevoAuthenticationError,
    BrevoRestrictedSenderError,
    BrevoValidationError,
    BrevoRateLimitError,
    BrevoDeliveryError,
)
from app.core.security import verify_password, get_password_hash, get_client_ip, get_client_user_agent
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/smtp-status", response_model=ApiResponse[dict])
def get_smtp_status():
    """Returns safe diagnostic configuration status of the email service (Resend HTTPS API / SMTP)."""
    status_data = email_service.get_status()
    return ApiResponse(
        success=True,
        message="Email service status retrieved",
        data=status_data,
    )


@router.get("/email-status", response_model=ApiResponse[dict])
def get_email_status():
    """Returns safe diagnostic configuration status of the active email service."""
    status_data = email_service.get_status()
    return ApiResponse(
        success=True,
        message="Email service status retrieved",
        data=status_data,
    )


@router.post("/register/send-otp", response_model=ApiResponse[dict])
def send_registration_otp(payload: SendOtpRequest, db: Session = Depends(get_db)):
    try:
        res = auth_service.send_registration_otp(db, email=payload.email, full_name=payload.full_name)
        return ApiResponse(success=True, message=res["message"], data=res)
    except (EmailNotConfiguredError, SMTPNotConfiguredError, ResendNotConfiguredError, BrevoNotConfiguredError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except (ResendRestrictedRecipientError, BrevoRestrictedSenderError) as e:
        detail_msg = (
            "Email verification delivery is restricted. "
            "Please verify that the sender email or domain is verified in your email provider console. "
            "Please contact the clinic administrator."
        ) if isinstance(e, BrevoRestrictedSenderError) else (
            "Email verification delivery is restricted for this recipient address. "
            "In sandbox mode, emails can only be sent to the registered Resend account owner. "
            "A custom domain must be verified in Resend to send to external recipients. "
            "Please contact the clinic administrator."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg,
        )
    except (ResendRateLimitError, BrevoRateLimitError) as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Email provider rate limit reached. Please wait a moment before requesting another code.",
        )
    except (ResendValidationError, BrevoValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except (
        EmailConnectionError,
        EmailAuthenticationError,
        EmailDeliveryError,
        SMTPConnectionError,
        SMTPAuthenticationError,
        SMTPDeliveryError,
        ResendConnectionError,
        ResendAuthenticationError,
        ResendDeliveryError,
        BrevoConnectionError,
        BrevoAuthenticationError,
        BrevoDeliveryError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send verification code: {str(e)}")


@router.post("/register/verify-otp", response_model=ApiResponse[dict])
def verify_registration_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    try:
        auth_service.verify_registration_otp(db, email=payload.email, otp=payload.otp)
        return ApiResponse(success=True, message="Email successfully verified with OTP", data={"email": payload.email, "verified": True})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Verification failed: {str(e)}")


@router.post("/register", response_model=ApiResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
def register(reg_data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, reg_data)
        token = auth_service.create_token_for_user(user, db=db)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Registration successful",
            data=TokenResponse(access_token=token, token_type="bearer", user=user_resp)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")


@router.post("/register/doctor-request", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def request_doctor_access(payload: DoctorAccessRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.request_doctor_access(db, payload)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Your Doctor account request has been submitted for verification. An administrator will review your medical credentials.",
            data=user_resp
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Doctor request submission failed: {str(e)}")


@router.post("/register/frontdesk-request", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def request_frontdesk_access(payload: FrontDeskAccessRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.request_frontdesk_access(db, payload)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Your Front Desk staff request has been submitted for administrator approval.",
            data=user_resp
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Front Desk request submission failed: {str(e)}")


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_client_user_agent(request)
    norm_email = login_data.email.strip().lower()

    cand_user = db.query(User).filter(User.email == norm_email).first()
    if not cand_user or not verify_password(login_data.password, cand_user.password_hash):
        if cand_user:
            cand_user.failed_login_attempts = (cand_user.failed_login_attempts or 0) + 1
            db.commit()
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            user_id=cand_user.id if cand_user else None,
            user_email=norm_email,
            clinic_id=cand_user.clinic_id if cand_user else None,
            severity="WARNING",
            ip_address=ip,
            user_agent=ua,
            details={"method": "password", "outcome": "failed", "reason": "invalid_credentials"}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not cand_user.is_active:
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            user_id=cand_user.id,
            user_email=norm_email,
            clinic_id=cand_user.clinic_id,
            severity="WARNING",
            ip_address=ip,
            user_agent=ua,
            details={"method": "password", "outcome": "failed", "reason": "account_disabled"}
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")

    user = cand_user
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    db.commit()

    token = auth_service.create_token_for_user(user, ip_address=ip, user_agent=ua, db=db)
    SecurityPrivacyService.record_security_event(
        db=db,
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        user_email=user.email,
        clinic_id=user.clinic_id,
        severity="INFO",
        ip_address=ip,
        user_agent=ua,
        details={"method": "password", "outcome": "success"}
    )
    user_resp = auth_service.format_user_response(db, user)
    return ApiResponse(
        success=True,
        message="Login successful",
        data=TokenResponse(access_token=token, token_type="bearer", user=user_resp)
    )


@router.post("/login/send-otp", response_model=ApiResponse[dict])
def send_login_otp(payload: LoginSendOtpRequest, db: Session = Depends(get_db)):
    try:
        res = auth_service.send_login_otp(db, email=payload.email)
        return ApiResponse(success=True, message=res["message"], data=res)
    except (EmailNotConfiguredError, SMTPNotConfiguredError, ResendNotConfiguredError, BrevoNotConfiguredError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except (ResendRestrictedRecipientError, BrevoRestrictedSenderError) as e:
        detail_msg = (
            "Email verification delivery is restricted. "
            "Please verify that the sender email or domain is verified in your email provider console. "
            "Please contact the clinic administrator."
        ) if isinstance(e, BrevoRestrictedSenderError) else (
            "Email verification delivery is restricted for this recipient address. "
            "In sandbox mode, emails can only be sent to the registered Resend account owner. "
            "A custom domain must be verified in Resend to send to external recipients. "
            "Please contact the clinic administrator."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg,
        )
    except (ResendRateLimitError, BrevoRateLimitError) as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Email provider rate limit reached. Please wait a moment before requesting another code.",
        )
    except (ResendValidationError, BrevoValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except (
        EmailConnectionError,
        EmailAuthenticationError,
        EmailDeliveryError,
        SMTPConnectionError,
        SMTPAuthenticationError,
        SMTPDeliveryError,
        ResendConnectionError,
        ResendAuthenticationError,
        ResendDeliveryError,
        BrevoConnectionError,
        BrevoAuthenticationError,
        BrevoDeliveryError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login/verify-otp", response_model=ApiResponse[TokenResponse])
def verify_login_otp(payload: LoginVerifyOtpRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_client_user_agent(request)
    norm_email = payload.email.strip().lower()
    cand_user = db.query(User).filter(User.email == norm_email).first()
    try:
        user = auth_service.verify_login_otp(db, email=norm_email, otp=payload.otp)
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        db.commit()

        token = auth_service.create_token_for_user(user, ip_address=ip, user_agent=ua, db=db)
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_SUCCESS",
            user_id=user.id,
            user_email=user.email,
            clinic_id=user.clinic_id,
            severity="INFO",
            ip_address=ip,
            user_agent=ua,
            details={"method": "email_otp", "outcome": "success"}
        )
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="OTP Login successful",
            data=TokenResponse(access_token=token, token_type="bearer", user=user_resp)
        )
    except ValueError as e:
        if cand_user:
            cand_user.failed_login_attempts = (cand_user.failed_login_attempts or 0) + 1
            db.commit()
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            user_id=cand_user.id if cand_user else None,
            user_email=norm_email,
            clinic_id=cand_user.clinic_id if cand_user else None,
            severity="WARNING",
            ip_address=ip,
            user_agent=ua,
            details={"method": "email_otp", "outcome": "failed", "reason": "invalid_or_expired_otp"}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/google", response_model=ApiResponse[TokenResponse])
def authenticate_google(payload: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_client_user_agent(request)
    token = payload.id_token or payload.credential
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google authentication token or credential is required")
    try:
        user = auth_service.authenticate_google(db, token=token, requested_role=payload.role or "PATIENT")
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        db.commit()

        access_token = auth_service.create_token_for_user(user, ip_address=ip, user_agent=ua, db=db)
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_SUCCESS",
            user_id=user.id,
            user_email=user.email,
            clinic_id=user.clinic_id,
            severity="INFO",
            ip_address=ip,
            user_agent=ua,
            details={"method": "google_sso", "outcome": "success"}
        )
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Google authentication successful",
            data=TokenResponse(access_token=access_token, token_type="bearer", user=user_resp)
        )
    except ValueError as e:
        SecurityPrivacyService.record_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            severity="WARNING",
            ip_address=ip,
            user_agent=ua,
            details={"method": "google_sso", "outcome": "failed", "reason": "invalid_token_or_conflict"}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/logout", response_model=ApiResponse[dict])
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = get_client_user_agent(request)
    current_jti = getattr(current_user, "current_jti", None)
    if current_jti:
        SecurityPrivacyService.revoke_session(db, current_user.id, current_jti)

    SecurityPrivacyService.record_security_event(
        db=db,
        event_type="LOGOUT",
        user_id=current_user.id,
        user_email=current_user.email,
        clinic_id=current_user.clinic_id,
        severity="INFO",
        ip_address=ip,
        user_agent=ua,
        details={"outcome": "success"}
    )
    return ApiResponse(success=True, message="Session revoked and logged out successfully")


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_resp = auth_service.format_user_response(db, current_user)
    return ApiResponse(success=True, data=user_resp)


@router.patch("/change-password", response_model=ApiResponse[dict])
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect")
    
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return ApiResponse(success=True, message="Password updated successfully")
