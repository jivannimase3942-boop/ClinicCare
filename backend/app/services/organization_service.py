import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.organization import Organization, Branch
from app.models.clinic import Clinic
from app.models.user import User, Doctor, Patient
from app.models.appointment import Appointment
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    BranchCreate,
    BranchUpdate,
    StaffInviteRequest,
)
from app.core.security import get_password_hash
from app.services.audit_service import audit_service


class OrganizationService:
    @staticmethod
    def get_organization(db: Session, org_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    @staticmethod
    def get_organization_by_code(db: Session, code: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.code == code.upper().strip()).first()

    @staticmethod
    def list_organizations(db: Session, skip: int = 0, limit: int = 50) -> List[Organization]:
        return db.query(Organization).offset(skip).limit(limit).all()

    @staticmethod
    def create_organization(
        db: Session, org_in: OrganizationCreate, creator_user: Optional[User] = None
    ) -> Organization:
        normalized_code = org_in.code.upper().strip()
        existing = db.query(Organization).filter(Organization.code == normalized_code).first()
        if existing:
            raise ValueError(f"Organization code '{normalized_code}' is already taken")

        org = Organization(
            name=org_in.name.strip(),
            code=normalized_code,
            description=org_in.description,
            email=str(org_in.email).strip().lower() if org_in.email else None,
            phone=org_in.phone.strip() if org_in.phone else None,
            website=org_in.website.strip() if org_in.website else None,
            headquarters_address=org_in.headquarters_address,
            is_active=org_in.is_active,
        )
        db.add(org)
        db.flush()

        audit_service.log_event(
            db=db,
            user_id=creator_user.id if creator_user else None,
            user_name=creator_user.full_name if creator_user else "System",
            action="CREATE",
            resource_type="ORGANIZATION",
            resource_id=org.id,
            details=f"Created healthcare organization: {org.name} ({org.code})",
        )
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def update_organization(
        db: Session, org_id: str, org_in: OrganizationUpdate, actor_user: Optional[User] = None
    ) -> Organization:
        org = OrganizationService.get_organization(db, org_id)
        if not org:
            raise ValueError(f"Organization with ID {org_id} not found")

        update_data = org_in.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if key == "email" and val:
                val = str(val).strip().lower()
            setattr(org, key, val)

        audit_service.log_event(
            db=db,
            user_id=actor_user.id if actor_user else None,
            user_name=actor_user.full_name if actor_user else "System",
            action="UPDATE",
            resource_type="ORGANIZATION",
            resource_id=org.id,
            details=f"Updated healthcare organization: {org.name}",
        )
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_branch(db: Session, branch_id: str) -> Optional[Branch]:
        return db.query(Branch).filter(Branch.id == branch_id).first()

    @staticmethod
    def list_branches(
        db: Session,
        organization_id: Optional[str] = None,
        user: Optional[User] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Branch]:
        query = db.query(Branch)

        # Scoping based on requesting user
        if user and user.role not in ["SUPER_ADMIN"]:
            if user.role == "ORGANIZATION_ADMIN" and user.organization_id:
                query = query.filter(Branch.organization_id == user.organization_id)
            elif user.branch_id:
                # Strictly isolate regular branch admins/staff to their own branch
                query = query.filter(Branch.id == user.branch_id)
            elif user.clinic_id:
                query = query.filter(Branch.clinic_id == user.clinic_id)

        if organization_id:
            query = query.filter(Branch.organization_id == organization_id)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_branch(
        db: Session,
        org_id: str,
        branch_in: BranchCreate,
        creator_user: Optional[User] = None,
    ) -> Branch:
        org = OrganizationService.get_organization(db, org_id)
        if not org:
            raise ValueError(f"Organization with ID {org_id} not found")

        normalized_code = branch_in.code.upper().strip()
        existing = db.query(Branch).filter(
            Branch.organization_id == org_id,
            Branch.code == normalized_code
        ).first()
        if existing:
            raise ValueError(f"Branch code '{normalized_code}' already exists under this organization")

        # Provision or link clinic tenant to preserve existing Clinic-based features
        clinic_id = branch_in.clinic_id
        if not clinic_id:
            # Auto-create linked Clinic tenant
            slug_base = f"{org.code.lower()}-{normalized_code.lower()}"
            clinic = Clinic(
                name=f"{org.name} - {branch_in.name}",
                slug=f"{slug_base}-{str(uuid.uuid4())[:6]}",
                address=branch_in.address,
                city=branch_in.city,
                state=branch_in.state,
                pincode=branch_in.pincode,
                phone=branch_in.phone,
                email=str(branch_in.email) if branch_in.email else None,
                operating_hours=branch_in.operating_hours,
                organization_id=org.id,
                is_active=branch_in.is_active,
            )
            db.add(clinic)
            db.flush()
            clinic_id = clinic.id
        else:
            # Link existing clinic to organization
            clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
            if clinic and not clinic.organization_id:
                clinic.organization_id = org.id

        branch = Branch(
            organization_id=org.id,
            clinic_id=clinic_id,
            name=branch_in.name.strip(),
            code=normalized_code,
            address=branch_in.address,
            city=branch_in.city,
            state=branch_in.state,
            pincode=branch_in.pincode,
            phone=branch_in.phone,
            email=str(branch_in.email).strip().lower() if branch_in.email else None,
            operating_hours=branch_in.operating_hours,
            branch_admin_user_id=branch_in.branch_admin_user_id,
            is_active=branch_in.is_active,
        )
        db.add(branch)
        db.flush()

        # If branch_admin_user_id is provided, associate that user
        if branch.branch_admin_user_id:
            admin_user = db.query(User).filter(User.id == branch.branch_admin_user_id).first()
            if admin_user:
                admin_user.organization_id = org.id
                admin_user.branch_id = branch.id
                admin_user.clinic_id = clinic_id
                admin_user.role = "BRANCH_ADMIN"

        audit_service.log_event(
            db=db,
            user_id=creator_user.id if creator_user else None,
            user_name=creator_user.full_name if creator_user else "System",
            action="CREATE",
            resource_type="BRANCH",
            resource_id=branch.id,
            clinic_id=clinic_id,
            details=f"Created branch '{branch.name}' ({branch.code}) under organization '{org.name}'",
        )
        db.commit()
        db.refresh(branch)
        return branch

    @staticmethod
    def update_branch(
        db: Session,
        branch_id: str,
        branch_in: BranchUpdate,
        actor_user: Optional[User] = None,
    ) -> Branch:
        branch = OrganizationService.get_branch(db, branch_id)
        if not branch:
            raise ValueError(f"Branch with ID {branch_id} not found")

        update_data = branch_in.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if key == "email" and val:
                val = str(val).strip().lower()
            setattr(branch, key, val)

        if "branch_admin_user_id" in update_data and branch.branch_admin_user_id:
            admin_user = db.query(User).filter(User.id == branch.branch_admin_user_id).first()
            if admin_user:
                admin_user.organization_id = branch.organization_id
                admin_user.branch_id = branch.id
                admin_user.clinic_id = branch.clinic_id
                admin_user.role = "BRANCH_ADMIN"

        audit_service.log_event(
            db=db,
            user_id=actor_user.id if actor_user else None,
            user_name=actor_user.full_name if actor_user else "System",
            action="UPDATE",
            resource_type="BRANCH",
            resource_id=branch.id,
            clinic_id=branch.clinic_id,
            details=f"Updated branch '{branch.name}'",
        )
        db.commit()
        db.refresh(branch)
        return branch

    @staticmethod
    def get_branch_stats(db: Session, branch: Branch) -> Dict[str, Any]:
        """Calculates branch-level KPIs ensuring tenant & branch scoping."""
        clinic_id = branch.clinic_id

        doctors_count = db.query(User).filter(
            User.role == "DOCTOR",
            User.is_active == True,
            (User.branch_id == branch.id) | (User.clinic_id == clinic_id)
        ).count()

        appointments_count = 0
        if clinic_id:
            appointments_count = db.query(Appointment).filter(
                Appointment.clinic_id == clinic_id
            ).count()

        staff_count = db.query(User).filter(
            User.is_active == True,
            User.role != "PATIENT",
            (User.branch_id == branch.id) | (User.clinic_id == clinic_id)
        ).count()

        return {
            "doctors_count": doctors_count,
            "appointments_count": appointments_count,
            "staff_count": staff_count,
        }

    @staticmethod
    def invite_staff(
        db: Session,
        invite: StaffInviteRequest,
        actor_user: User,
    ) -> User:
        """
        Invites or creates a staff member under controlled administrator provisioning.
        Public registration for staff is forbidden.
        """
        normalized_email = invite.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError(f"User with email '{normalized_email}' already exists")

        # Determine target branch and organization
        target_branch = None
        if invite.branch_id:
            target_branch = db.query(Branch).filter(Branch.id == invite.branch_id).first()
            if not target_branch:
                raise ValueError(f"Branch '{invite.branch_id}' not found")
        elif actor_user.branch_id:
            target_branch = db.query(Branch).filter(Branch.id == actor_user.branch_id).first()

        org_id = target_branch.organization_id if target_branch else actor_user.organization_id
        clinic_id = target_branch.clinic_id if target_branch else actor_user.clinic_id

        # Verification of actor's authority:
        # Branch admin cannot invite outside their branch
        if actor_user.role == "BRANCH_ADMIN" and target_branch and actor_user.branch_id != target_branch.id:
            raise ValueError("Branch administrators can only provision staff for their own assigned branch")

        raw_password = invite.temporary_password or f"Staff@{uuid.uuid4().hex[:6].capitalize()}1!"
        user = User(
            email=normalized_email,
            password_hash=get_password_hash(raw_password),
            full_name=invite.full_name.strip(),
            phone=invite.phone,
            role=invite.role.upper().strip(),
            organization_id=org_id,
            branch_id=target_branch.id if target_branch else None,
            clinic_id=clinic_id,
            is_active=True,
        )
        db.add(user)
        db.flush()

        audit_service.log_event(
            db=db,
            user_id=actor_user.id,
            user_name=actor_user.full_name,
            action="CREATE",
            resource_type="STAFF_INVITE",
            resource_id=user.id,
            clinic_id=clinic_id,
            details=f"Invited staff member '{user.full_name}' as {user.role} to branch {target_branch.name if target_branch else 'N/A'}",
        )
        db.commit()
        db.refresh(user)
        return user


organization_service = OrganizationService()
