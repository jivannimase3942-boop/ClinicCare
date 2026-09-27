from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, PasswordChangeRequest
from app.services.auth_service import auth_service
from app.core.security import verify_password, get_password_hash
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
