from fastapi import APIRouter, Depends, HTTPException, status
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
from app.core.security import verify_password, get_password_hash
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/send-otp", response_model=ApiResponse[dict])
def send_registration_otp(payload: SendOtpRequest, db: Session = Depends(get_db)):
    try:
        res = auth_service.send_registration_otp(db, email=payload.email, full_name=payload.full_name)
        return ApiResponse(success=True, message=res["message"], data=res)
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
        token = auth_service.create_token_for_user(user)
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
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate_user(db, login_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        token = auth_service.create_token_for_user(user)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Login successful",
            data=TokenResponse(access_token=token, token_type="bearer", user=user_resp)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login/send-otp", response_model=ApiResponse[dict])
def send_login_otp(payload: LoginSendOtpRequest, db: Session = Depends(get_db)):
    try:
        res = auth_service.send_login_otp(db, email=payload.email)
        return ApiResponse(success=True, message=res["message"], data=res)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login/verify-otp", response_model=ApiResponse[TokenResponse])
def verify_login_otp(payload: LoginVerifyOtpRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.verify_login_otp(db, email=payload.email, otp=payload.otp)
        token = auth_service.create_token_for_user(user)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="OTP Login successful",
            data=TokenResponse(access_token=token, token_type="bearer", user=user_resp)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/google", response_model=ApiResponse[TokenResponse])
def authenticate_google(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    token = payload.id_token or payload.credential
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google authentication token or credential is required")
    try:
        user = auth_service.authenticate_google(db, token=token, requested_role=payload.role or "PATIENT")
        access_token = auth_service.create_token_for_user(user)
        user_resp = auth_service.format_user_response(db, user)
        return ApiResponse(
            success=True,
            message="Google authentication successful",
            data=TokenResponse(access_token=access_token, token_type="bearer", user=user_resp)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
