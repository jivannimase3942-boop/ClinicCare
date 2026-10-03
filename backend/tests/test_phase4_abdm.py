import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, Patient, Doctor
from app.models.organization import Organization, Branch
from app.models.abdm import ABHAProfile, ABDMConsentArtifact, FacilityRegistryProfile, ProfessionalRegistryProfile
from app.core.security import create_access_token


@pytest.fixture
def auth_tokens(db_session: Session):
    """
    Creates test users and returns JWT access tokens for patient, doctor, admin.
    """
    db = db_session
    # Patient
    patient_user = db.query(User).filter(User.email == "patient_abdm@hospital.com").first()
    if not patient_user:
        patient_user = User(
            email="patient_abdm@hospital.com",
            password_hash="hashed_test_password_123",
            full_name="ABDM Test Patient",
            role="PATIENT",
            is_active=True,
        )
        db.add(patient_user)
        db.commit()
        db.refresh(patient_user)

    patient_profile = db.query(Patient).filter(Patient.user_id == patient_user.id).first()
    if not patient_profile:
        patient_profile = Patient(user_id=patient_user.id)
        db.add(patient_profile)
        db.commit()
        db.refresh(patient_profile)

    # Doctor
    doctor_user = db.query(User).filter(User.email == "dr_abdm@hospital.com").first()
    if not doctor_user:
        doctor_user = User(
            email="dr_abdm@hospital.com",
            password_hash="hashed_test_password_123",
            full_name="Dr. ABDM Specialist",
            role="DOCTOR",
            is_active=True,
        )
        db.add(doctor_user)
        db.commit()
        db.refresh(doctor_user)

    from app.models.user import Department
    dept = db.query(Department).first()
    if not dept:
        dept = Department(name="General Medicine", description="General OPD")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    doctor_profile = db.query(Doctor).filter(Doctor.user_id == doctor_user.id).first()
    if not doctor_profile:
        doctor_profile = Doctor(
            user_id=doctor_user.id,
            department_id=dept.id,
            specialization="General Medicine",
            qualification="MBBS, MD",
            experience_years=8,
            consultation_fee=500.0,
        )
        db.add(doctor_profile)
        db.commit()
        db.refresh(doctor_profile)

    # Admin
    admin_user = db.query(User).filter(User.email == "admin_abdm@hospital.com").first()
    if not admin_user:
        admin_user = User(
            email="admin_abdm@hospital.com",
            password_hash="hashed_test_password_123",
            full_name="ABDM Admin Officer",
            role="ADMIN",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    # Organization & Branch
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="ABDM Healthcare Org", code="ORG-ABDM-01")
        db.add(org)
        db.commit()
        db.refresh(org)

    branch = db.query(Branch).filter(Branch.name == "ABDM Test Branch").first()
    if not branch:
        branch = Branch(
            organization_id=org.id,
            name="ABDM Test Branch",
            code="BR-ABDM-01",
            city="Pune",
            state="Maharashtra",
            phone="+91 20 5555 1234",
            email="abdm.branch@hospital.com",
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)

    return {
        "patient": (create_access_token({"sub": patient_user.id, "email": patient_user.email, "role": "PATIENT"}), patient_user, patient_profile),
        "doctor": (create_access_token({"sub": doctor_user.id, "email": doctor_user.email, "role": "DOCTOR"}), doctor_user, doctor_profile),
        "admin": (create_access_token({"sub": admin_user.id, "email": admin_user.email, "role": "ADMIN"}), admin_user),
        "branch": branch,
    }


def test_abdm_gateway_status_honest_disclosure(client):
    resp = client.get("/api/abdm/status")
    assert resp.status_code == 200
    data = resp.json().get("data", {})
    # Without credentials, must report integration_configured = False
    assert data["integration_configured"] is False
    assert "not provisioned" in data["notice"].lower() or "gateway" in data["notice"].lower()
    assert "OPConsultation" in data["supported_hi_types"]
    assert "Prescription" in data["supported_hi_types"]


def test_patient_abha_profile_retrieval_and_init(client, auth_tokens):
    p_token, p_user, p_prof = auth_tokens["patient"]
    hdr = {"Authorization": f"Bearer {p_token}"}

    resp = client.get("/api/abdm/patient/abha", headers=hdr)
    assert resp.status_code == 200
    data = resp.json().get("data", {})
    assert data["patient_id"] == p_prof.id
    assert data["verification_status"] == "NOT_LINKED"
    assert data["kyc_verified"] is False


def test_abha_auth_initiation_without_credentials_does_not_fake_government_otp(client, auth_tokens):
    p_token, p_user, p_prof = auth_tokens["patient"]
    hdr = {"Authorization": f"Bearer {p_token}"}

    payload = {
        "auth_mode": "MOBILE_OTP",
        "identifier": "+919876543210",
    }
    resp = client.post("/api/abdm/patient/abha/initiate-auth", json=payload, headers=hdr)
    assert resp.status_code == 200
    data = resp.json().get("data", {})
    # Strict rule: DO NOT fake government OTP or claim integration works when credentials are absent
    assert data["integration_configured"] is False
    assert data["status"] == "GATEWAY_NOT_CONFIGURED"
    assert "credentials" in data["message"].lower() or "not configured" in data["message"].lower()


def test_abdm_consent_request_and_lifecycle(client, auth_tokens):
    p_token, p_user, p_prof = auth_tokens["patient"]
    d_token, d_user, d_prof = auth_tokens["doctor"]

    # Doctor requests consent from patient
    doc_hdr = {"Authorization": f"Bearer {d_token}"}
    req_payload = {
        "patient_id": p_prof.id,
        "purpose_code": "CAREMGT",
        "purpose_text": "Care Management for Specialist Consultation",
        "hi_types": ["OPConsultation", "Prescription"],
    }
    resp = client.post("/api/abdm/consents/request", json=req_payload, headers=doc_hdr)
    assert resp.status_code == 200
    artifact = resp.json().get("data", {})
    assert artifact["status"] == "REQUESTED"
    assert artifact["consent_request_id"].startswith("CR-")
    consent_id = artifact["id"]

    # Patient lists consents
    pat_hdr = {"Authorization": f"Bearer {p_token}"}
    list_resp = client.get("/api/abdm/consents", headers=pat_hdr)
    assert list_resp.status_code == 200
    consents = list_resp.json().get("data", [])
    assert any(c["id"] == consent_id for c in consents)

    # Patient grants consent
    grant_resp = client.post(f"/api/abdm/consents/{consent_id}/status?new_status=GRANTED", headers=pat_hdr)
    assert grant_resp.status_code == 200
    assert grant_resp.json().get("data", {}).get("status") == "GRANTED"

    # Patient can revoke consent
    revoke_resp = client.post(f"/api/abdm/consents/{consent_id}/status?new_status=REVOKED", headers=pat_hdr)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json().get("data", {}).get("status") == "REVOKED"


def test_facility_registry_hfr_management_and_rbac(client, auth_tokens):
    admin_token, admin_user = auth_tokens["admin"]
    p_token, p_user, _ = auth_tokens["patient"]
    branch = auth_tokens["branch"]

    adm_hdr = {"Authorization": f"Bearer {admin_token}"}
    pat_hdr = {"Authorization": f"Bearer {p_token}"}

    # Patient is forbidden from configuring facility HFR
    hfr_payload = {
        "branch_id": branch.id,
        "facility_name": "ClinicCare Central Multispeciality Hospital",
        "hfr_id": "IN-MH-100892",
        "facility_type": "HOSPITAL",
        "system_of_medicine": "ALLOPATHY",
        "state_code": "MH",
        "district_code": "Pune",
        "pincode": "411001",
    }
    forbidden_resp = client.post("/api/abdm/facility-registry", json=hfr_payload, headers=pat_hdr)
    assert forbidden_resp.status_code == 403

    # Admin registers branch HFR
    reg_resp = client.post("/api/abdm/facility-registry", json=hfr_payload, headers=adm_hdr)
    assert reg_resp.status_code == 200
    hfr_data = reg_resp.json().get("data", {})
    assert hfr_data["hfr_id"] == "IN-MH-100892"
    assert hfr_data["verification_status"] == "APPLIED"

    # Query registry
    get_resp = client.get(f"/api/abdm/facility-registry?branch_id={branch.id}", headers=adm_hdr)
    assert get_resp.status_code == 200
    assert len(get_resp.json().get("data", [])) >= 1


def test_doctor_professional_registry_hpr_and_rbac(client, auth_tokens):
    d_token, d_user, d_prof = auth_tokens["doctor"]
    p_token, p_user, _ = auth_tokens["patient"]

    doc_hdr = {"Authorization": f"Bearer {d_token}"}
    pat_hdr = {"Authorization": f"Bearer {p_token}"}

    # Patient blocked from updating doctor's HPR
    hpr_payload = {
        "doctor_id": d_prof.id,
        "hpr_id": "14-9876-5432-1098@hpr",
        "registration_number": "MMC-2018-09-1234",
        "state_medical_council": "Maharashtra Medical Council",
        "year_of_registration": "2018",
        "system_of_medicine": "ALLOPATHY",
    }
    pat_blocked = client.post("/api/abdm/professional-registry", json=hpr_payload, headers=pat_hdr)
    assert pat_blocked.status_code == 403

    # Doctor registers their own HPR credentials
    doc_resp = client.post("/api/abdm/professional-registry", json=hpr_payload, headers=doc_hdr)
    assert doc_resp.status_code == 200
    hpr_data = doc_resp.json().get("data", {})
    assert hpr_data["hpr_id"] == "14-9876-5432-1098@hpr"
    assert hpr_data["registration_number"] == "MMC-2018-09-1234"
    assert hpr_data["state_medical_council"] == "Maharashtra Medical Council"

    # Query doctor HPR
    query_resp = client.get(f"/api/abdm/professional-registry/{d_prof.id}", headers=doc_hdr)
    assert query_resp.status_code == 200
    assert query_resp.json().get("data", {})["registration_number"] == "MMC-2018-09-1234"
