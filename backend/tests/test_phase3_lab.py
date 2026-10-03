import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, Doctor, Patient


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


def test_lab_catalog_management(client, doctor_headers):
    # Doctor adds a diagnostic test to the catalog
    test_payload = {
        "name": "Complete Blood Count (CBC)",
        "code": "CBC01",
        "category": "HEMATOLOGY",
        "sample_type": "Whole Blood EDTA",
        "turnaround_hours": 12,
        "price": 350.0,
        "normal_range": "Variable by parameter",
        "unit": "Various"
    }
    res = client.post("/api/lab/tests", json=test_payload, headers=doctor_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["name"] == "Complete Blood Count (CBC)"
    assert data["code"] == "CBC01"
    assert data["price"] == 350.0

    # Search tests
    res_list = client.get("/api/lab/tests?search=CBC", headers=doctor_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1


def test_lab_order_workflow_to_release(client, doctor_headers, patient_headers):
    # 1. First ensure we have a test in the catalog
    test_payload = {
        "name": "Fasting Blood Sugar (FBS)",
        "code": "FBS01",
        "category": "BIOCHEMISTRY",
        "sample_type": "Fluoride Plasma",
        "turnaround_hours": 6,
        "price": 120.0,
        "normal_range": "70 - 99 mg/dL",
        "unit": "mg/dL"
    }
    res_t = client.post("/api/lab/tests", json=test_payload, headers=doctor_headers)
    assert res_t.status_code == 201
    test_id = res_t.json()["data"]["id"]

    # Retrieve patient ID
    db = SessionLocal()
    pat = db.query(Patient).first()
    patient_id = pat.id
    db.close()

    # 2. Doctor places lab order
    order_payload = {
        "patient_id": patient_id,
        "test_ids": [test_id],
        "priority": "ROUTINE",
        "clinical_notes": "Screening for Type-2 Diabetes Mellitus"
    }
    res_order = client.post("/api/lab/orders", json=order_payload, headers=doctor_headers)
    assert res_order.status_code == 201
    order_data = res_order.json()["data"]
    order_id = order_data["id"]
    assert order_data["status"] == "ORDERED"
    assert len(order_data["samples"]) > 0
    sample_id = order_data["samples"][0]["id"]
    assert order_data["samples"][0]["barcode_number"].startswith("SMP-")

    # 3. Sample collection
    res_sample = client.post(f"/api/lab/samples/{sample_id}/collect", headers=doctor_headers)
    assert res_sample.status_code == 200
    assert res_sample.json()["data"]["status"] == "SAMPLE_COLLECTED"

    # 4. Result entry
    results_payload = {
        "results": [
            {
                "lab_test_id": test_id,
                "parameter_name": "Fasting Glucose",
                "result_value": "115",
                "unit": "mg/dL",
                "reference_range": "70 - 99",
                "is_abnormal": True,
                "technician_notes": "Impaired fasting glycaemia noted"
            }
        ]
    }
    res_results = client.post(f"/api/lab/orders/{order_id}/results", json=results_payload, headers=doctor_headers)
    assert res_results.status_code == 200
    assert res_results.json()["data"]["status"] == "RESULT_READY"

    # 5. Pathologist validates & releases report
    release_payload = {
        "summary_notes": "Mild hyperglycemia noted. Advise HbA1c and physician consultation."
    }
    res_release = client.post(f"/api/lab/orders/{order_id}/release", json=release_payload, headers=doctor_headers)
    assert res_release.status_code == 200
    report_data = res_release.json()["data"]
    assert report_data["is_released"] is True
    assert report_data["is_validated"] is True
    assert report_data["report_number"].startswith("LRP-")

    # 6. Patient accesses their released lab report
    res_pat = client.get(f"/api/lab/orders/{order_id}", headers=patient_headers)
    assert res_pat.status_code == 200
    pat_order = res_pat.json()["data"]
    assert pat_order["report"] is not None
    assert pat_order["report"]["is_released"] is True
    assert len(pat_order["results"]) == 1
