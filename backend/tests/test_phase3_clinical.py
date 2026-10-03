import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.clinic import Clinic
from app.models.user import User, Doctor, Patient, Department
from app.models.clinical import ConsultationRecord, VitalSign
from app.models.audit import AuditLog
from app.core.security import get_password_hash


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post("/api/auth/login", json={"email": "doctor@hospital.com", "password": "Doctor@123"})
    assert res.status_code == 200, f"Doctor login failed: {res.text}"
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def patient_headers(client):
    res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert res.status_code == 200, f"Patient login failed: {res.text}"
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_vitals_recording_and_bmi(client, auth_headers, patient_headers):
    # Get primary patient
    db = SessionLocal()
    patient = db.query(Patient).first()
    assert patient is not None
    patient_id = patient.id
    db.close()

    vitals_payload = {
        "patient_id": patient_id,
        "temperature_celsius": 37.2,
        "pulse_bpm": 76,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "respiratory_rate": 16,
        "spo2_percent": 99.0,
        "weight_kg": 70.0,
        "height_cm": 175.0,
        "notes": "Patient feeling well, regular vitals."
    }

    # Doctor records vitals
    res = client.post("/api/clinical/vitals", json=vitals_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["bp_systolic"] == 120
    assert data["bp_diastolic"] == 80
    assert data["pulse_bpm"] == 76
    # BMI = 70 / (1.75 ** 2) = 22.857 -> rounded to 22.9
    assert data["bmi"] == 22.9

    # Patient retrieves own vitals
    res_pat = client.get(f"/api/clinical/patients/{patient_id}/vitals", headers=patient_headers)
    assert res_pat.status_code == 200
    assert len(res_pat.json()["data"]) >= 1


def test_consultation_lifecycle_draft_to_finalized(client, auth_headers, patient_headers):
    db = SessionLocal()
    patient = db.query(Patient).first()
    assert patient is not None
    patient_id = patient.id
    db.close()

    create_payload = {
        "patient_id": patient_id,
        "chief_complaint": "Persistent dry cough and mild fever for 3 days",
        "history_of_present_illness": "Symptoms started on Wednesday, no shortness of breath.",
        "medical_history": "No known chronic illnesses",
        "allergies": "NKDA (No known drug allergies)",
        "examination_notes": "Chest clear, throat slightly erythematous.",
        "diagnosis": "Acute Upper Respiratory Tract Infection (URTI)",
        "treatment_plan": "Hydration, symptomatic paracetamol, warm saline gargles.",
        "follow_up_date": (date.today() + timedelta(days=5)).isoformat(),
        "clinical_notes": "Advised to return if temperature exceeds 38.5C."
    }

    # 1. Doctor creates consultation draft
    res_create = client.post("/api/clinical/consultations", json=create_payload, headers=auth_headers)
    assert res_create.status_code == 201
    draft = res_create.json()["data"]
    consultation_id = draft["id"]
    assert draft["status"] == "DRAFT"
    assert draft["is_finalized"] is False
    assert draft["version"] == 1

    # 2. Patient cannot view draft consultation
    res_pat_draft = client.get(f"/api/clinical/consultations/{consultation_id}", headers=patient_headers)
    assert res_pat_draft.status_code == 403

    # 3. Doctor updates consultation draft
    update_payload = {
        "treatment_plan": "Hydration, symptomatic paracetamol, warm saline gargles, steam inhalation."
    }
    res_update = client.patch(f"/api/clinical/consultations/{consultation_id}", json=update_payload, headers=auth_headers)
    assert res_update.status_code == 200
    updated = res_update.json()["data"]
    assert updated["version"] == 2
    assert "steam inhalation" in updated["treatment_plan"]

    # 4. Doctor finalizes consultation
    res_fin = client.post(f"/api/clinical/consultations/{consultation_id}/finalize", headers=auth_headers)
    assert res_fin.status_code == 200
    finalized = res_fin.json()["data"]
    assert finalized["status"] == "FINALIZED"
    assert finalized["is_finalized"] is True
    assert finalized["finalized_at"] is not None

    # 5. Overwriting finalized consultation is rejected to protect medical records
    res_reedit = client.patch(f"/api/clinical/consultations/{consultation_id}", json={"diagnosis": "New Diagnosis"}, headers=auth_headers)
    assert res_reedit.status_code == 400

    # 6. Patient can now view finalized consultation
    res_pat_fin = client.get(f"/api/clinical/consultations/{consultation_id}", headers=patient_headers)
    assert res_pat_fin.status_code == 200
    assert res_pat_fin.json()["data"]["is_finalized"] is True


def test_patient_timeline_and_rbac_isolation(client, auth_headers, patient_headers, admin_headers):
    db = SessionLocal()
    primary_patient = db.query(Patient).first()
    assert primary_patient is not None
    p_id = primary_patient.id

    # Create a secondary test patient for privacy verification
    sec_user = db.query(User).filter(User.email == "sec_patient@test.com").first()
    if not sec_user:
        clinic_id = primary_patient.user.clinic_id if primary_patient.user else None
        sec_user = User(
            email="sec_patient@test.com",
            password_hash=get_password_hash("Password@123"),
            full_name="Secondary Isolated Patient",
            role="PATIENT",
            is_active=True,
            clinic_id=clinic_id
        )
        db.add(sec_user)
        db.flush()
        sec_pat = Patient(user_id=sec_user.id, date_of_birth=date(1995, 1, 1), gender="Male")
        db.add(sec_pat)
        db.commit()
    else:
        sec_pat = db.query(Patient).filter(Patient.user_id == sec_user.id).first()
    sec_p_id = sec_pat.id
    db.close()

    # 1. Primary patient accesses own timeline
    res_own = client.get(f"/api/clinical/patients/{p_id}/timeline", headers=patient_headers)
    assert res_own.status_code == 200
    timeline = res_own.json()["data"]
    assert "events" in timeline
    assert timeline["patient_id"] == p_id

    # 2. Primary patient attempts to access secondary patient's timeline (Must be 403 Forbidden)
    res_other = client.get(f"/api/clinical/patients/{sec_p_id}/timeline", headers=patient_headers)
    assert res_other.status_code == 403

    # 3. Doctor can access timeline for patient care
    res_doc = client.get(f"/api/clinical/patients/{p_id}/timeline", headers=auth_headers)
    assert res_doc.status_code == 200

    # 4. Check audit log has recorded clinical actions
    res_audit = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()["data"]
    actions = [l["action"] for l in logs]
    assert "CONSULTATION_CREATE" in actions
    assert "CONSULTATION_FINALIZE" in actions
    assert "VITAL_RECORD" in actions
