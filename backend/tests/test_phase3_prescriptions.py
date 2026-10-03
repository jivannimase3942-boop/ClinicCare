import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, Doctor, Patient
from app.models.prescription import Medicine, Prescription
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


def test_medicine_master_catalog(client, doctor_headers):
    # Doctor adds a new medicine
    med_payload = {
        "brand_name": "Amoxyclav 625",
        "generic_name": "Amoxicillin and Potassium Clavulanate",
        "strength": "625 mg",
        "dosage_form": "TABLET",
        "manufacturer": "Sun Pharma",
        "category": "ANTIBIOTIC",
        "hsn_code": "3004",
        "gst_rate_percent": 12.0,
        "unit_price": 22.50
    }
    res_add = client.post("/api/prescriptions/medicines", json=med_payload, headers=doctor_headers)
    assert res_add.status_code == 201
    med_data = res_add.json()["data"]
    assert med_data["brand_name"] == "Amoxyclav 625"
    assert med_data["unit_price"] == 22.50

    # Search medicine catalog
    res_search = client.get("/api/prescriptions/medicines?search=Amoxyclav", headers=doctor_headers)
    assert res_search.status_code == 200
    results = res_search.json()["data"]
    assert any(m["brand_name"] == "Amoxyclav 625" for m in results)


def test_digital_prescription_creation_and_supervision(client, doctor_headers, patient_headers, admin_headers):
    db = SessionLocal()
    patient = db.query(Patient).first()
    assert patient is not None
    patient_id = patient.id
    db.close()

    rx_payload = {
        "patient_id": patient_id,
        "diagnosis_summary": "Bacterial Sinusitis and Acute Rhinitis",
        "general_advice": "Rest, drink plenty of warm fluids, steam inhalation twice daily.",
        "diet_lifestyle_notes": "Avoid cold foods and carbonated drinks.",
        "follow_up_date": (date.today() + timedelta(days=7)).isoformat(),
        "items": [
            {
                "medicine_name": "Amoxyclav 625",
                "generic_name": "Amoxicillin and Potassium Clavulanate",
                "dosage_form": "TABLET",
                "strength": "625 mg",
                "dosage": "1 tablet",
                "frequency": "1-0-1 (Twice daily)",
                "duration": "5 days",
                "route": "ORAL",
                "instructions": "After meals",
                "quantity": 10
            },
            {
                "medicine_name": "Dolo 650",
                "generic_name": "Paracetamol",
                "dosage_form": "TABLET",
                "strength": "650 mg",
                "dosage": "1 tablet",
                "frequency": "SOS (For body ache or fever > 38C)",
                "duration": "3 days",
                "route": "ORAL",
                "instructions": "After meals",
                "quantity": 6
            }
        ]
    }

    # 1. Doctor creates prescription draft
    res_create = client.post("/api/prescriptions", json=rx_payload, headers=doctor_headers)
    assert res_create.status_code == 201
    draft = res_create.json()["data"]
    rx_id = draft["id"]
    assert draft["status"] == "DRAFT"
    assert draft["is_finalized"] is False
    assert len(draft["items"]) == 2
    assert draft["prescription_number"].startswith("RX-")

    # 2. Patient cannot view unfinalized prescription draft
    res_pat_block = client.get(f"/api/prescriptions/{rx_id}", headers=patient_headers)
    assert res_pat_block.status_code == 403

    # 3. Doctor finalizes and signs the prescription
    res_fin = client.post(f"/api/prescriptions/{rx_id}/finalize", headers=doctor_headers)
    assert res_fin.status_code == 200
    finalized = res_fin.json()["data"]
    assert finalized["status"] == "ISSUED"
    assert finalized["is_finalized"] is True
    assert finalized["finalized_at"] is not None

    # 4. Patient can now view finalized prescription
    res_pat_ok = client.get(f"/api/prescriptions/{rx_id}", headers=patient_headers)
    assert res_pat_ok.status_code == 200
    pat_rx = res_pat_ok.json()["data"]
    assert pat_rx["is_finalized"] is True
    assert len(pat_rx["items"]) == 2

    # 5. Check audit log records prescription lifecycle
    res_audit = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert res_audit.status_code == 200
    actions = [l["action"] for l in res_audit.json()["data"]]
    assert "PRESCRIPTION_CREATE" in actions
    assert "PRESCRIPTION_FINALIZE" in actions
