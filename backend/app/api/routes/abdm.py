from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.abdm import (
    ABDMStatusResponse,
    ABHAProfileResponse,
    ABHAAuthInitiateRequest,
    ABHAAuthInitiateResponse,
    ABDMConsentCreateRequest,
    ABDMConsentResponse,
    FacilityRegistryCreateRequest,
    FacilityRegistryResponse,
    ProfessionalRegistryCreateRequest,
    ProfessionalRegistryResponse,
)
from app.models.user import User
from app.services.abdm_service import abdm_service
from app.api.dependencies import (
    get_current_user,
    get_current_patient,
    require_roles,
)

router = APIRouter(prefix="", tags=["ABDM & Interoperability"])


@router.get("/abdm/status", response_model=ApiResponse[ABDMStatusResponse])
def get_abdm_gateway_status():
    """
    Public / Authenticated status check for ABDM Gateway readiness.
    Provides honest disclosure of integration status without fake claims.
    """
    status_resp = abdm_service.get_status()
    return ApiResponse(success=True, data=status_resp)


@router.get("/abdm/patient/abha", response_model=ApiResponse[ABHAProfileResponse])
def get_my_abha_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves or initializes the ABHA profile for the authenticated patient.
    """
    if current_user.role != "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ABHA patient profile is reserved for patient accounts",
        )
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    profile = abdm_service.get_or_create_patient_abha(db, current_user.patient_profile.id)
    return ApiResponse(success=True, data=profile)


@router.post("/abdm/patient/abha/initiate-auth", response_model=ApiResponse[ABHAAuthInitiateResponse])
def initiate_abha_authentication(
    req: ABHAAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiates real Aadhaar / Mobile OTP session for ABHA linking.
    If sandbox credentials are not configured, transparently returns integration_configured: False.
    """
    if current_user.role != "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ABHA authentication is only available for patient accounts",
        )
    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    result = abdm_service.initiate_abha_auth(
        db,
        patient_id=current_user.patient_profile.id,
        auth_mode=req.auth_mode,
        identifier=req.identifier,
    )
    return ApiResponse(success=True, data=result)


@router.get("/abdm/consents", response_model=ApiResponse[List[ABDMConsentResponse]])
def list_abdm_consents(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists ABDM electronic consent artifacts.
    Patients view only their own; Doctors / Admins can query by patient_id.
    """
    if current_user.role == "PATIENT":
        if not current_user.patient_profile:
            return ApiResponse(success=True, data=[])
        target_patient_id = current_user.patient_profile.id
    else:
        if not patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinicians and staff must specify patient_id query parameter",
            )
        target_patient_id = patient_id

    consents = abdm_service.get_patient_consents(db, target_patient_id)
    return ApiResponse(success=True, data=consents)


@router.post("/abdm/consents/request", response_model=ApiResponse[ABDMConsentResponse])
def create_abdm_consent_request(
    req: ABDMConsentCreateRequest,
    current_user: User = Depends(require_roles(["DOCTOR", "ADMIN", "ORGANIZATION_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    Initiates an ABDM Consent Request artifact to request patient medical history.
    """
    artifact = abdm_service.create_consent_artifact(db, req, current_user)
    return ApiResponse(
        success=True,
        message="ABDM consent request dispatched to patient",
        data=artifact,
    )


@router.post("/abdm/consents/{consent_id}/status", response_model=ApiResponse[ABDMConsentResponse])
def update_abdm_consent_status(
    consent_id: str,
    new_status: str = Query(..., pattern="^(GRANTED|DENIED|REVOKED|EXPIRED)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Patient grants, denies, or revokes electronic consent artifact.
    """
    artifact = abdm_service.update_consent_status(db, consent_id, new_status, current_user)
    return ApiResponse(
        success=True,
        message=f"ABDM consent status updated to {new_status}",
        data=artifact,
    )


# -------------------------------------------------------------
# Health Facility Registry (HFR) Endpoints
# -------------------------------------------------------------
@router.get("/abdm/facility-registry", response_model=ApiResponse[List[FacilityRegistryResponse]])
def get_facility_registry(
    branch_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns registered HFR facility profiles.
    """
    profiles = abdm_service.get_facility_registry(db, branch_id=branch_id, clinic_id=clinic_id)
    return ApiResponse(success=True, data=profiles)


@router.post("/abdm/facility-registry", response_model=ApiResponse[FacilityRegistryResponse])
def register_or_update_facility_hfr(
    req: FacilityRegistryCreateRequest,
    current_user: User = Depends(require_roles(["ADMIN", "ORGANIZATION_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    Configures or updates official Health Facility Registry (HFR) identifier for branch or clinic.
    """
    profile = abdm_service.register_or_update_facility(db, req, current_user)
    return ApiResponse(
        success=True,
        message="Facility HFR configuration saved successfully",
        data=profile,
    )


# -------------------------------------------------------------
# Healthcare Professional Registry (HPR) Endpoints
# -------------------------------------------------------------
@router.get("/abdm/professional-registry/{doctor_id}", response_model=ApiResponse[Optional[ProfessionalRegistryResponse]])
def get_doctor_hpr(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns official HPR credentials and state medical council registration for a doctor.
    """
    profile = abdm_service.get_doctor_hpr(db, doctor_id)
    return ApiResponse(success=True, data=profile)


@router.post("/abdm/professional-registry", response_model=ApiResponse[ProfessionalRegistryResponse])
def register_or_update_doctor_hpr(
    req: ProfessionalRegistryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Registers or updates Healthcare Professional Registry (HPR) and State Medical Council details.
    Restricted to the doctor themselves or authorized admins.
    """
    profile = abdm_service.register_or_update_doctor_hpr(db, req, current_user)
    return ApiResponse(
        success=True,
        message="Healthcare Professional Registry (HPR) details saved successfully",
        data=profile,
    )
