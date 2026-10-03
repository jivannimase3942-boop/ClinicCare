from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    StaffInviteRequest,
)
from app.schemas.auth import UserResponse
from app.models.user import User
from app.models.organization import Organization, Branch
from app.services.organization_service import organization_service
from app.api.dependencies import get_current_user, require_roles, verify_branch_access


router = APIRouter(prefix="", tags=["Organizations & Branches"])


# -------------------------------------------------------------
# Organization Endpoints
# -------------------------------------------------------------

@router.get("/organizations", response_model=ApiResponse[List[OrganizationResponse]])
def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    try:
        if current_user.role == "ORGANIZATION_ADMIN" and current_user.organization_id:
            org = organization_service.get_organization(db, current_user.organization_id)
            orgs = [org] if org else []
        else:
            orgs = organization_service.list_organizations(db, skip=skip, limit=limit)
        
        result = []
        for org in orgs:
            branches_resp = [
                BranchResponse.model_validate(b) for b in org.branches
            ]
            org_dict = OrganizationResponse(
                id=org.id,
                name=org.name,
                code=org.code,
                description=org.description,
                email=org.email,
                phone=org.phone,
                website=org.website,
                headquarters_address=org.headquarters_address,
                is_active=org.is_active,
                created_at=org.created_at,
                updated_at=org.updated_at,
                branches=branches_resp,
            )
            result.append(org_dict)
            
        return ApiResponse(success=True, message="Organizations retrieved successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/organizations", response_model=ApiResponse[OrganizationResponse], status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    try:
        org = organization_service.create_organization(db, payload, creator_user=current_user)
        resp = OrganizationResponse.model_validate(org)
        return ApiResponse(success=True, message=f"Organization '{org.name}' created successfully", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organizations/{org_id}", response_model=ApiResponse[OrganizationResponse])
def get_organization(
    org_id: str,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    if current_user.role == "ORGANIZATION_ADMIN" and current_user.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization")
    
    org = organization_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
    branches_resp = [BranchResponse.model_validate(b) for b in org.branches]
    resp = OrganizationResponse(
        id=org.id,
        name=org.name,
        code=org.code,
        description=org.description,
        email=org.email,
        phone=org.phone,
        website=org.website,
        headquarters_address=org.headquarters_address,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
        branches=branches_resp,
    )
    return ApiResponse(success=True, message="Organization retrieved", data=resp)


@router.put("/organizations/{org_id}", response_model=ApiResponse[OrganizationResponse])
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    if current_user.role == "ORGANIZATION_ADMIN" and current_user.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization")

    try:
        org = organization_service.update_organization(db, org_id, payload, actor_user=current_user)
        resp = OrganizationResponse.model_validate(org)
        return ApiResponse(success=True, message="Organization updated", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -------------------------------------------------------------
# Branch Endpoints
# -------------------------------------------------------------

@router.get("/branches", response_model=ApiResponse[List[BranchResponse]])
def list_branches(
    organization_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        branches = organization_service.list_branches(
            db, organization_id=organization_id, user=current_user, skip=skip, limit=limit
        )
        data = []
        for b in branches:
            stats = organization_service.get_branch_stats(db, b)
            b_resp = BranchResponse(
                id=b.id,
                organization_id=b.organization_id,
                clinic_id=b.clinic_id,
                name=b.name,
                code=b.code,
                address=b.address,
                city=b.city,
                state=b.state,
                pincode=b.pincode,
                phone=b.phone,
                email=b.email,
                operating_hours=b.operating_hours,
                branch_admin_user_id=b.branch_admin_user_id,
                is_active=b.is_active,
                created_at=b.created_at,
                updated_at=b.updated_at,
                stats=stats,
            )
            data.append(b_resp)
        return ApiResponse(success=True, message="Branches retrieved", data=data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/organizations/{org_id}/branches", response_model=ApiResponse[BranchResponse], status_code=status.HTTP_201_CREATED)
def create_branch(
    org_id: str,
    payload: BranchCreate,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN"])),
    db: Session = Depends(get_db),
):
    if current_user.role == "ORGANIZATION_ADMIN" and current_user.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create branch outside your organization")

    try:
        branch = organization_service.create_branch(db, org_id, payload, creator_user=current_user)
        stats = organization_service.get_branch_stats(db, branch)
        resp = BranchResponse(
            id=branch.id,
            organization_id=branch.organization_id,
            clinic_id=branch.clinic_id,
            name=branch.name,
            code=branch.code,
            address=branch.address,
            city=branch.city,
            state=branch.state,
            pincode=branch.pincode,
            phone=branch.phone,
            email=branch.email,
            operating_hours=branch.operating_hours,
            branch_admin_user_id=branch.branch_admin_user_id,
            is_active=branch.is_active,
            created_at=branch.created_at,
            updated_at=branch.updated_at,
            stats=stats,
        )
        return ApiResponse(success=True, message=f"Branch '{branch.name}' created successfully", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/branches/{branch_id}", response_model=ApiResponse[BranchResponse])
def get_branch_details(
    branch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Enforces strict branch-level isolation
    branch = verify_branch_access(db, current_user, branch_id)
    stats = organization_service.get_branch_stats(db, branch)
    resp = BranchResponse(
        id=branch.id,
        organization_id=branch.organization_id,
        clinic_id=branch.clinic_id,
        name=branch.name,
        code=branch.code,
        address=branch.address,
        city=branch.city,
        state=branch.state,
        pincode=branch.pincode,
        phone=branch.phone,
        email=branch.email,
        operating_hours=branch.operating_hours,
        branch_admin_user_id=branch.branch_admin_user_id,
        is_active=branch.is_active,
        created_at=branch.created_at,
        updated_at=branch.updated_at,
        stats=stats,
    )
    return ApiResponse(success=True, message="Branch retrieved", data=resp)


@router.put("/branches/{branch_id}", response_model=ApiResponse[BranchResponse])
def update_branch(
    branch_id: str,
    payload: BranchUpdate,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN", "BRANCH_ADMIN"])),
    db: Session = Depends(get_db),
):
    branch = verify_branch_access(db, current_user, branch_id)
    try:
        updated = organization_service.update_branch(db, branch.id, payload, actor_user=current_user)
        stats = organization_service.get_branch_stats(db, updated)
        resp = BranchResponse(
            id=updated.id,
            organization_id=updated.organization_id,
            clinic_id=updated.clinic_id,
            name=updated.name,
            code=updated.code,
            address=updated.address,
            city=updated.city,
            state=updated.state,
            pincode=updated.pincode,
            phone=updated.phone,
            email=updated.email,
            operating_hours=updated.operating_hours,
            branch_admin_user_id=updated.branch_admin_user_id,
            is_active=updated.is_active,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            stats=stats,
        )
        return ApiResponse(success=True, message="Branch updated successfully", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/branches/{branch_id}/staff", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def invite_branch_staff(
    branch_id: str,
    payload: StaffInviteRequest,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN", "BRANCH_ADMIN"])),
    db: Session = Depends(get_db),
):
    branch = verify_branch_access(db, current_user, branch_id)
    payload.branch_id = branch.id
    try:
        user = organization_service.invite_staff(db, payload, actor_user=current_user)
        return ApiResponse(
            success=True,
            message=f"Staff member '{user.full_name}' successfully provisioned for branch '{branch.name}'",
            data={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "branch_id": branch.id,
                "branch_name": branch.name,
                "clinic_id": user.clinic_id,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/branches/{branch_id}/staff", response_model=ApiResponse[List[dict]])
def list_branch_staff(
    branch_id: str,
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "ADMIN", "BRANCH_ADMIN"])),
    db: Session = Depends(get_db),
):
    branch = verify_branch_access(db, current_user, branch_id)
    staff_members = db.query(User).filter(
        User.is_active == True,
        User.role != "PATIENT",
        (User.branch_id == branch.id) | (User.clinic_id == branch.clinic_id)
    ).all()

    data = [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "phone": u.phone,
            "branch_id": u.branch_id,
            "clinic_id": u.clinic_id,
            "is_active": u.is_active,
        }
        for u in staff_members
    ]
    return ApiResponse(success=True, message="Branch staff retrieved", data=data)
