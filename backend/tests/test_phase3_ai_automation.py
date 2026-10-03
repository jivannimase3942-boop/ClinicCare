import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, Patient, Doctor
from app.models.clinic import Clinic
from app.models.lab import LabOrder, LabTest, LabReport
from app.core.security import get_password_hash


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def doctor_headers(client):
    res = client.post("/api/auth/login", json={"email": "doctor@hospital.com", "password": "Doctor@123"})
    assert res.status_code == 200
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def patient_headers(client):
    res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert res.status_code == 200
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert res.status_code == 200
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_clinical_drafting_guardrail(client, doctor_headers, patient_headers):
    db = SessionLocal()
    pat = db.query(Patient).first()
    patient_id = pat.id
    db.close()

    draft_payload = {
        "patient_id": patient_id,
        "raw_notes": "Patient complains of productive cough and low grade evening fever for 4 days.\nHistory of allergic rhinitis.\nVitals stable, no wheezing on auscultation."
    }

    # 1. Doctor requests draft note
    res = client.post("/api/ai/clinical/draft-note", json=draft_payload, headers=doctor_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_ai_draft"] is True
    assert data["requires_human_verification"] is True
    assert "Does NOT constitute a finalized diagnosis" in data["disclaimer"]
    assert "productive cough" in data["chief_complaint"].lower()

    # 2. Patient attempting to access clinical drafting is blocked (RBAC enforcement)
    res_pat = client.post("/api/ai/clinical/draft-note", json=draft_payload, headers=patient_headers)
    assert res_pat.status_code == 403


def test_ai_lab_report_summarization_and_safety(client, doctor_headers):
    import uuid
    # Setup released lab report
    db = SessionLocal()
    doc = db.query(Doctor).first()
    pat = db.query(Patient).first()
    clinic_id = doc.user.clinic_id or "default"

    unique_suffix = uuid.uuid4().hex[:6].upper()
    order = LabOrder(
        clinic_id=clinic_id,
        patient_id=pat.id,
        doctor_id=doc.id,
        order_number=f"LAB-AI-{unique_suffix}",
        status="VALIDATED"
    )
    db.add(order)
    db.flush()

    report = LabReport(
        clinic_id=clinic_id,
        lab_order_id=order.id,
        patient_id=pat.id,
        report_number=f"LRP-AI-{unique_suffix}",
        is_validated=True,
        is_released=True,
        summary_notes="Thyroid function parameters within normal clinical limits."
    )
    db.add(report)
    db.commit()
    order_id = order.id
    db.close()

    # Summarize released report
    res_sum = client.post("/api/ai/clinical/summarize-report", json={"order_id": order_id}, headers=doctor_headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()["data"]
    assert "AI-generated summary. Please review the original report." in sum_data["summary"]
    assert sum_data["disclaimer"] == "AI-generated summary. Please review the original report."


def test_automation_event_engine_and_honest_providers(client, admin_headers):
    # 1. Check supported automation events and provider statuses
    res_cap = client.get("/api/automation/events", headers=admin_headers)
    assert res_cap.status_code == 200
    cap_data = res_cap.json()["data"]
    assert "APPOINTMENT_BOOKED" in cap_data["supported_events"]
    assert "LAB_RESULT_READY" in cap_data["supported_events"]
    assert "in_app" in cap_data["providers_configured"]

    # Retrieve patient user
    db = SessionLocal()
    pat = db.query(Patient).first()
    pat_user_id = pat.user_id
    db.close()

    # 2. Trigger automated event
    trigger_payload = {
        "event_name": "LAB_RESULT_READY",
        "recipient_user_id": pat_user_id,
        "title": "Lab Results Ready for Review",
        "message": "Your diagnostic test results have been released by the laboratory.",
        "payload": {
            "order_number": "LAB-202610-0001",
            "phone": "+91 98765 00000"
        }
    }
    res_trig = client.post("/api/automation/events/trigger", json=trigger_payload, headers=admin_headers)
    assert res_trig.status_code == 200
    res_data = res_trig.json()["data"]
    channels = res_data["channels"]

    # In-app notification delivered
    assert channels["in_app"]["status"] == "delivered"
    assert "notification_id" in channels["in_app"]

    # WhatsApp reports honest configuration state (not fake delivery)
    assert "whatsapp" in channels
    if not channels["whatsapp"].get("configured", False):
        assert channels["whatsapp"]["status"] == "unconfigured"

    # Email & SMS report honest configuration
    assert channels["email"]["status"] == "unconfigured"
    assert channels["sms"]["status"] == "unconfigured"

    # 3. Invalid event is rejected
    bad_payload = {
        "event_name": "NON_EXISTENT_HEALTHCARE_EVENT",
        "recipient_user_id": pat_user_id
    }
    res_bad = client.post("/api/automation/events/trigger", json=bad_payload, headers=admin_headers)
    assert res_bad.status_code == 400


def test_clinical_analytics_tenant_scoped(client, admin_headers):
    # 1. Admin queries clinical analytics
    res = client.get("/api/admin/clinical-analytics", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "patient_metrics" in data
    assert "doctor_metrics" in data
    assert "lab_metrics" in data
    assert "pharmacy_metrics" in data

    # 2. Tenant isolation check for analytics
    db = SessionLocal()
    clinic_b = db.query(Clinic).filter(Clinic.slug == "clinic-analytics-b").first()
    if not clinic_b:
        clinic_b = Clinic(name="Analytics Clinic B", slug="clinic-analytics-b", is_active=True)
        db.add(clinic_b)
        db.flush()

    user_b = db.query(User).filter(User.email == "admin_analytics_b@hospital.com").first()
    if not user_b:
        user_b = User(
            email="admin_analytics_b@hospital.com",
            password_hash=get_password_hash("Admin@123"),
            full_name="Admin Analytics B",
            role="ADMIN",
            clinic_id=clinic_b.id,
            is_active=True,
        )
        db.add(user_b)
        db.commit()
    clinic_b_id = clinic_b.id
    db.close()

    res_b = client.post("/api/auth/login", json={"email": "admin_analytics_b@hospital.com", "password": "Admin@123"})
    assert res_b.status_code == 200
    headers_b = {"Authorization": f"Bearer {res_b.json()['data']['access_token']}"}

    # Query analytics for Clinic B (isolated empty clinic)
    res_analytics_b = client.get("/api/admin/clinical-analytics", headers=headers_b)
    assert res_analytics_b.status_code == 200
    data_b = res_analytics_b.json()["data"]
    assert data_b["clinic_id"] == clinic_b_id
    assert data_b["patient_metrics"]["total_patients"] == 0
    assert data_b["pharmacy_metrics"]["active_batches"] == 0
