from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.clinic import (
    ClinicOnboardRequest,
    ClinicOnboardResponse,
    ClinicResponse,
    ClinicPublicResponse,
    ClinicUpdateRequest,
)
from app.services.clinic_service import clinic_service
from app.api.dependencies import get_current_user, get_optional_user, require_roles
from app.models.user import User
from app.models.clinic import Clinic

router = APIRouter(prefix="/clinics", tags=["Clinics & Multi-Tenancy"])


@router.post("/onboard", response_model=ApiResponse[ClinicOnboardResponse], status_code=status.HTTP_201_CREATED)
def onboard_new_clinic(
    payload: ClinicOnboardRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        res = clinic_service.onboard_clinic(db, payload, client_ip=client_ip, user_agent=user_agent)
        return ApiResponse(success=True, message=res.message, data=res)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Onboarding failed: {str(e)}")


@router.get("/current", response_model=ApiResponse[ClinicResponse])
def get_current_clinic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_clinic_id = current_user.clinic_id
    if not target_clinic_id:
        # Fall back to default central clinic
        default_c = clinic_service.get_or_create_default_clinic(db)
        target_clinic_id = default_c.id

    clinic = clinic_service.get_clinic_by_id(db, target_clinic_id)
    if not clinic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic profile not found")

    resp = ClinicResponse(
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
    return ApiResponse(success=True, data=resp)


@router.patch("/current", response_model=ApiResponse[ClinicResponse])
def update_current_clinic(
    data: ClinicUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(["ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    target_clinic_id = current_user.clinic_id
    if not target_clinic_id:
        default_c = clinic_service.get_or_create_default_clinic(db)
        target_clinic_id = default_c.id

    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        updated = clinic_service.update_clinic(
            db=db,
            clinic_id=target_clinic_id,
            data=data,
            current_user=current_user,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        resp = ClinicResponse(
            id=updated.id,
            name=updated.name,
            slug=updated.slug,
            phone=updated.phone,
            email=updated.email,
            address=updated.address,
            city=updated.city,
            state=updated.state,
            pincode=updated.pincode,
            country=updated.country,
            operating_hours=updated.operating_hours,
            consultation_fee_default=float(updated.consultation_fee_default),
            is_active=updated.is_active,
            settings_json=updated.settings_json,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
        return ApiResponse(success=True, message="Clinic profile updated", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/public/{slug}", response_model=ApiResponse[ClinicPublicResponse])
def get_public_clinic_profile(slug: str, db: Session = Depends(get_db)):
    clinic = clinic_service.get_clinic_by_slug(db, slug)
    if not clinic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Clinic with slug '{slug}' not found")

    settings = {}
    if clinic.settings_json:
        import json
        try:
            settings = json.loads(clinic.settings_json)
        except Exception:
            settings = {}
    dept_names = settings.get("departments") or ([d.name for d in clinic.departments if d.is_active] if clinic.departments else [])

    resp = ClinicPublicResponse(
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
        departments=dept_names,
    )
    return ApiResponse(success=True, data=resp)


@router.get("", response_model=ApiResponse[List[ClinicResponse]])
def list_clinics(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    clinics = clinic_service.list_clinics(db, active_only=active_only)
    resp = [
        ClinicResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            phone=c.phone,
            email=c.email,
            address=c.address,
            city=c.city,
            state=c.state,
            pincode=c.pincode,
            country=c.country,
            operating_hours=c.operating_hours,
            consultation_fee_default=float(c.consultation_fee_default),
            is_active=c.is_active,
            settings_json=c.settings_json,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in clinics
    ]
    return ApiResponse(success=True, data=resp)
