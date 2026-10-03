import pytest
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.organization import Organization, Branch
from app.models.clinic import Clinic


@pytest.fixture
def org_test_setup(db_session):
    # 1. Super Admin
    super_admin = User(
        email="superadmin@cliniccare.com",
        password_hash=get_password_hash("Super@123"),
        full_name="Super Administrator",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db_session.add(super_admin)

    # 2. Org 1: Apollo Care Network
    org1 = Organization(
        name="Apollo Care Network",
        code="APOLLO",
        email="hq@apollocare.com",
        phone="+919876543210",
        headquarters_address="Apollo Towers, Bengaluru",
        is_active=True,
    )
    db_session.add(org1)
    db_session.flush()

    # Org 1 Admin
    org1_admin = User(
        email="org1admin@apollocare.com",
        password_hash=get_password_hash("Org1@123"),
        full_name="Apollo Network Admin",
        role="ORGANIZATION_ADMIN",
        organization_id=org1.id,
        is_active=True,
    )
    db_session.add(org1_admin)
    db_session.flush()

    # Clinic 1 & Clinic 2 for branches
    clinic_a = Clinic(name="Apollo Indiranagar Clinic", slug="apollo-indiranagar", organization_id=org1.id, is_active=True)
    clinic_b = Clinic(name="Apollo Whitefield Clinic", slug="apollo-whitefield", organization_id=org1.id, is_active=True)
    db_session.add_all([clinic_a, clinic_b])
    db_session.flush()

    # Branch A (Indiranagar)
    branch_a = Branch(
        organization_id=org1.id,
        clinic_id=clinic_a.id,
        name="Indiranagar Specialty Branch",
        code="IND-01",
        city="Bengaluru",
        state="Karnataka",
        operating_hours="08:00 AM - 08:00 PM",
        is_active=True,
    )
    # Branch B (Whitefield)
    branch_b = Branch(
        organization_id=org1.id,
        clinic_id=clinic_b.id,
        name="Whitefield Campus Branch",
        code="WHI-01",
        city="Bengaluru",
        state="Karnataka",
        operating_hours="09:00 AM - 09:00 PM",
        is_active=True,
    )
    db_session.add_all([branch_a, branch_b])
    db_session.flush()

    # Branch A Admin
    branch_a_admin = User(
        email="branch_a_admin@apollocare.com",
        password_hash=get_password_hash("BranchA@123"),
        full_name="Branch A Manager",
        role="BRANCH_ADMIN",
        organization_id=org1.id,
        branch_id=branch_a.id,
        clinic_id=clinic_a.id,
        is_active=True,
    )
    # Branch B Admin
    branch_b_admin = User(
        email="branch_b_admin@apollocare.com",
        password_hash=get_password_hash("BranchB@123"),
        full_name="Branch B Manager",
        role="BRANCH_ADMIN",
        organization_id=org1.id,
        branch_id=branch_b.id,
        clinic_id=clinic_b.id,
        is_active=True,
    )
    db_session.add_all([branch_a_admin, branch_b_admin])
    db_session.flush()

    branch_a.branch_admin_user_id = branch_a_admin.id
    branch_b.branch_admin_user_id = branch_b_admin.id

    # Org 2: Manipal Health Group (Competitor)
    org2 = Organization(
        name="Manipal Health Group",
        code="MANIPAL",
        email="contact@manipalhealth.com",
        is_active=True,
    )
    db_session.add(org2)
    db_session.flush()

    org2_admin = User(
        email="org2admin@manipalhealth.com",
        password_hash=get_password_hash("Org2@123"),
        full_name="Manipal Lead Admin",
        role="ORGANIZATION_ADMIN",
        organization_id=org2.id,
        is_active=True,
    )
    db_session.add(org2_admin)

    # Regular Patient
    patient = User(
        email="test_pat_user@cliniccare.com",
        password_hash=get_password_hash("Patient@123"),
        full_name="Regular Patient",
        role="PATIENT",
        is_active=True,
    )
    db_session.add(patient)

    db_session.commit()

    return {
        "super_admin": super_admin,
        "org1": org1,
        "org1_admin": org1_admin,
        "clinic_a": clinic_a,
        "clinic_b": clinic_b,
        "branch_a": branch_a,
        "branch_b": branch_b,
        "branch_a_admin": branch_a_admin,
        "branch_b_admin": branch_b_admin,
        "org2": org2,
        "org2_admin": org2_admin,
        "patient": patient,
    }


def auth_header(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_list_and_create_organizations(client, org_test_setup):
    super_admin = org_test_setup["super_admin"]
    headers = auth_header(super_admin)

    # 1. List organizations
    resp = client.get("/api/organizations", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    codes = [o["code"] for o in data]
    assert "APOLLO" in codes
    assert "MANIPAL" in codes

    # 2. Create organization
    create_payload = {
        "name": "Fortis Healthcare Chain",
        "code": "FORTIS",
        "email": "hq@fortishealthcare.com",
        "phone": "+918001234567",
        "city": "Gurugram",
        "is_active": True,
    }
    create_resp = client.post("/api/organizations", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["data"]["code"] == "FORTIS"


def test_create_branch_with_auto_provisioned_clinic(client, org_test_setup):
    org1 = org_test_setup["org1"]
    org1_admin = org_test_setup["org1_admin"]
    headers = auth_header(org1_admin)

    # Create new branch under Apollo
    branch_payload = {
        "name": "Apollo Koramangala OPD",
        "code": "KOR-01",
        "address": "80 Feet Road, 4th Block, Koramangala",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560034",
        "phone": "+919988776655",
        "operating_hours": "07:30 AM - 08:30 PM",
        "is_active": True,
    }
    resp = client.post(f"/api/organizations/{org1.id}/branches", json=branch_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["code"] == "KOR-01"
    assert data["clinic_id"] is not None  # Automatically provisioned clinic tenant!


def test_branch_isolation_enforcement(client, org_test_setup):
    branch_a = org_test_setup["branch_a"]
    branch_b = org_test_setup["branch_b"]
    branch_a_admin = org_test_setup["branch_a_admin"]
    branch_b_admin = org_test_setup["branch_b_admin"]
    headers_a = auth_header(branch_a_admin)
    headers_b = auth_header(branch_b_admin)

    # 1. Branch A Admin CAN view Branch A
    resp_a = client.get(f"/api/branches/{branch_a.id}", headers=headers_a)
    assert resp_a.status_code == 200
    assert resp_a.json()["data"]["name"] == branch_a.name

    # 2. Branch A Admin CANNOT view Branch B (Cross-branch access forbidden)
    resp_cross = client.get(f"/api/branches/{branch_b.id}", headers=headers_a)
    assert resp_cross.status_code == 403
    assert "Cross-branch access forbidden" in resp_cross.json()["detail"]

    # 3. Branch A Admin CANNOT update Branch B
    update_payload = {"name": "Malicious Branch Hijack"}
    resp_update = client.put(f"/api/branches/{branch_b.id}", json=update_payload, headers=headers_a)
    assert resp_update.status_code == 403

    # 4. Branch A Admin CANNOT invite staff to Branch B
    invite_payload = {
        "email": "infiltrator@apollocare.com",
        "full_name": "Infiltrator Staff",
        "role": "NURSE",
        "branch_id": branch_b.id,
    }
    resp_invite = client.post(f"/api/branches/{branch_b.id}/staff", json=invite_payload, headers=headers_a)
    assert resp_invite.status_code == 403


def test_organization_admin_multi_branch_access(client, org_test_setup):
    org1_admin = org_test_setup["org1_admin"]
    branch_a = org_test_setup["branch_a"]
    branch_b = org_test_setup["branch_b"]
    headers = auth_header(org1_admin)

    # Org Admin can view both branches in their organization
    resp_a = client.get(f"/api/branches/{branch_a.id}", headers=headers)
    assert resp_a.status_code == 200
    assert resp_a.json()["data"]["id"] == branch_a.id

    resp_b = client.get(f"/api/branches/{branch_b.id}", headers=headers)
    assert resp_b.status_code == 200
    assert resp_b.json()["data"]["id"] == branch_b.id

    # Org Admin lists all branches
    resp_list = client.get("/api/branches", headers=headers)
    assert resp_list.status_code == 200
    branch_ids = [b["id"] for b in resp_list.json()["data"]]
    assert branch_a.id in branch_ids
    assert branch_b.id in branch_ids


def test_cross_organization_isolation(client, org_test_setup):
    org1 = org_test_setup["org1"]
    org2_admin = org_test_setup["org2_admin"]
    headers = auth_header(org2_admin)

    # Org 2 Admin CANNOT view or manage Org 1
    resp = client.get(f"/api/organizations/{org1.id}", headers=headers)
    assert resp.status_code == 403

    # Org 2 Admin CANNOT create branches in Org 1
    payload = {
        "name": "Unauthorized Manipal Branch in Apollo",
        "code": "UNAUTH-01",
    }
    resp_create = client.post(f"/api/organizations/{org1.id}/branches", json=payload, headers=headers)
    assert resp_create.status_code == 403


def test_patient_and_public_privilege_blocking(client, org_test_setup):
    patient = org_test_setup["patient"]
    headers = auth_header(patient)

    # Patients cannot access admin organizations endpoint
    resp = client.get("/api/organizations", headers=headers)
    assert resp.status_code == 403

    # Public registration with privileged roles is blocked
    reg_payload = {
        "email": "hacker@evil.com",
        "password": "Password123!",
        "full_name": "Fake Admin",
        "role": "ORGANIZATION_ADMIN",
    }
    resp_reg = client.post("/api/auth/register", json=reg_payload)
    assert resp_reg.status_code == 400
    assert "cannot be registered through public registration" in resp_reg.json()["detail"].lower()


def test_cross_branch_staff_and_isolation(client, org_test_setup):
    branch_a = org_test_setup["branch_a"]
    branch_b = org_test_setup["branch_b"]
    branch_a_admin = org_test_setup["branch_a_admin"]
    branch_b_admin = org_test_setup["branch_b_admin"]
    headers_a = auth_header(branch_a_admin)
    headers_b = auth_header(branch_b_admin)

    # 1. Branch A admin cannot list staff of Branch B
    resp_b_staff_by_a = client.get(f"/api/branches/{branch_b.id}/staff", headers=headers_a)
    assert resp_b_staff_by_a.status_code == 403
    assert "Cross-branch access forbidden" in resp_b_staff_by_a.json()["detail"]

    # 2. Branch B admin cannot list staff of Branch A
    resp_a_staff_by_b = client.get(f"/api/branches/{branch_a.id}/staff", headers=headers_b)
    assert resp_a_staff_by_b.status_code == 403
    assert "Cross-branch access forbidden" in resp_a_staff_by_b.json()["detail"]

    # 3. Branch A admin can list their own staff
    resp_own_staff = client.get(f"/api/branches/{branch_a.id}/staff", headers=headers_a)
    assert resp_own_staff.status_code == 200
    assert resp_own_staff.json()["success"] is True

