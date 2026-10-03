import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, Patient
from app.models.prescription import Medicine


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
def admin_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert res.status_code == 200
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_supplier_and_batch_lifecycle(client, admin_headers):
    # 1. Register Supplier
    sup_payload = {
        "name": "MedPlus Pharma Distributors",
        "contact_person": "Ramesh Kumar",
        "phone": "+91 98765 43210",
        "email": "supply@medplus.in",
        "gstin": "27AABCU9603R1ZM",
        "dl_number": "MH-TZ-123456",
        "address": "Andheri East, Mumbai, Maharashtra"
    }
    res_sup = client.post("/api/pharmacy/suppliers", json=sup_payload, headers=admin_headers)
    assert res_sup.status_code == 201
    supplier_id = res_sup.json()["data"]["id"]

    # 2. Add Medicine to master
    med_payload = {
        "brand_name": "Azithral 500",
        "generic_name": "Azithromycin",
        "strength": "500 mg",
        "dosage_form": "TABLET",
        "manufacturer": "Alembic Pharma",
        "category": "ANTIBIOTIC",
        "hsn_code": "3004",
        "gst_rate_percent": 12.0,
        "unit_price": 25.0
    }
    res_med = client.post("/api/prescriptions/medicines", json=med_payload, headers=admin_headers)
    assert res_med.status_code == 201
    medicine_id = res_med.json()["data"]["id"]

    # 3. Add Stock Batch
    today = date.today()
    future_expiry = today + timedelta(days=365)
    batch_payload = {
        "medicine_id": medicine_id,
        "supplier_id": supplier_id,
        "batch_number": "AZT2026B1",
        "expiry_date": str(future_expiry),
        "purchase_price": 18.0,
        "mrp": 28.0,
        "sale_price": 25.0,
        "initial_quantity": 100,
        "reorder_threshold": 15
    }
    res_batch = client.post("/api/pharmacy/batches", json=batch_payload, headers=admin_headers)
    assert res_batch.status_code == 201
    batch_data = res_batch.json()["data"]
    batch_id = batch_data["id"]
    assert batch_data["current_quantity"] == 100
    assert batch_data["is_expired"] is False

    # 4. Check Auditable Transactions Ledger
    res_tx = client.get(f"/api/pharmacy/transactions?batch_id={batch_id}", headers=admin_headers)
    assert res_tx.status_code == 200
    txs = res_tx.json()["data"]
    assert len(txs) >= 1
    assert txs[0]["transaction_type"] == "PURCHASE"
    assert txs[0]["quantity"] == 100

    # 5. Manual Stock Adjustment (e.g. Damage)
    adj_payload = {
        "batch_id": batch_id,
        "transaction_type": "DAMAGE",
        "quantity": -5,
        "reason": "Water damage in storage rack 3"
    }
    res_adj = client.post("/api/pharmacy/adjustments", json=adj_payload, headers=admin_headers)
    assert res_adj.status_code == 200
    assert res_adj.json()["data"]["current_quantity"] == 95

    # 6. Negative inventory protection
    bad_adj = {
        "batch_id": batch_id,
        "transaction_type": "ADJUSTMENT",
        "quantity": -200,
        "reason": "Excess deduction attempt"
    }
    res_bad = client.post("/api/pharmacy/adjustments", json=bad_adj, headers=admin_headers)
    assert res_bad.status_code == 400


def test_dispense_billing_integration_and_expiry_guardrail(client, admin_headers):
    # Setup medicine and patient
    db = SessionLocal()
    pat = db.query(Patient).first()
    patient_id = pat.id
    db.close()

    med_payload = {
        "brand_name": "Paracip 650",
        "generic_name": "Paracetamol",
        "strength": "650 mg",
        "dosage_form": "TABLET",
        "category": "ANALGESIC",
        "unit_price": 3.0
    }
    res_med = client.post("/api/prescriptions/medicines", json=med_payload, headers=admin_headers)
    assert res_med.status_code == 201
    medicine_id = res_med.json()["data"]["id"]

    # 1. Valid non-expired batch
    today = date.today()
    valid_batch_payload = {
        "medicine_id": medicine_id,
        "batch_number": "PARA26V",
        "expiry_date": str(today + timedelta(days=180)),
        "purchase_price": 1.5,
        "mrp": 3.5,
        "sale_price": 3.0,
        "initial_quantity": 50,
        "reorder_threshold": 10
    }
    res_v = client.post("/api/pharmacy/batches", json=valid_batch_payload, headers=admin_headers)
    assert res_v.status_code == 201
    valid_batch_id = res_v.json()["data"]["id"]

    # 2. Expired batch to verify safety guardrail
    expired_batch_payload = {
        "medicine_id": medicine_id,
        "batch_number": "PARA25EXP",
        "expiry_date": str(today - timedelta(days=15)),
        "purchase_price": 1.5,
        "mrp": 3.5,
        "sale_price": 3.0,
        "initial_quantity": 20,
        "reorder_threshold": 5
    }
    res_exp = client.post("/api/pharmacy/batches", json=expired_batch_payload, headers=admin_headers)
    assert res_exp.status_code == 201
    expired_batch_id = res_exp.json()["data"]["id"]

    # 3. Check inventory alerts for expired batch
    res_alerts = client.get("/api/pharmacy/alerts", headers=admin_headers)
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()["data"]
    expired_alerts = [a for a in alerts if a["alert_type"] == "EXPIRED" and a["batch_id"] == expired_batch_id]
    assert len(expired_alerts) > 0
    assert expired_alerts[0]["severity"] == "HIGH"

    # 4. Attempt to dispense expired stock -> Must be blocked!
    dispense_expired_payload = {
        "patient_id": patient_id,
        "items": [
            {"batch_id": expired_batch_id, "quantity": 5}
        ],
        "payment_method": "CASH"
    }
    res_disp_exp = client.post("/api/pharmacy/dispense", json=dispense_expired_payload, headers=admin_headers)
    assert res_disp_exp.status_code == 400
    assert "Cannot dispense expired stock" in res_disp_exp.json()["detail"]

    # 5. Dispense valid stock -> Generates Invoice in existing Billing engine
    dispense_valid_payload = {
        "patient_id": patient_id,
        "items": [
            {"batch_id": valid_batch_id, "quantity": 10}
        ],
        "payment_method": "CASH",
        "notes": "Dispensed at pharmacy counter"
    }
    res_disp_valid = client.post("/api/pharmacy/dispense", json=dispense_valid_payload, headers=admin_headers)
    assert res_disp_valid.status_code == 201
    disp_data = res_disp_valid.json()["data"]
    assert disp_data["invoice_number"].startswith("INV-")
    assert disp_data["total_amount"] == 30.0  # 10 * 3.0
    assert disp_data["status"] == "PAID"

    # Verify batch quantity was deducted
    res_batch_check = client.get(f"/api/pharmacy/batches?medicine_id={medicine_id}", headers=admin_headers)
    assert res_batch_check.status_code == 200
    batches = res_batch_check.json()["data"]
    v_batch = next(b for b in batches if b["id"] == valid_batch_id)
    assert v_batch["current_quantity"] == 40  # 50 - 10


def test_pharmacy_tenant_isolation(client, admin_headers):
    # Setup second isolated clinic
    from app.models.clinic import Clinic
    from app.core.security import get_password_hash

    db = SessionLocal()
    clinic_b = db.query(Clinic).filter(Clinic.slug == "clinic-b-pharm").first()
    if not clinic_b:
        clinic_b = Clinic(name="Isolated Clinic B", slug="clinic-b-pharm", is_active=True)
        db.add(clinic_b)
        db.flush()

    user_b = db.query(User).filter(User.email == "admin_b_pharm@hospital.com").first()
    if not user_b:
        user_b = User(
            email="admin_b_pharm@hospital.com",
            password_hash=get_password_hash("Admin@123"),
            full_name="Admin Clinic B",
            role="ADMIN",
            clinic_id=clinic_b.id,
            is_active=True,
        )
        db.add(user_b)
        db.commit()
    db.close()

    # Login as Clinic B Admin
    res_b = client.post("/api/auth/login", json={"email": "admin_b_pharm@hospital.com", "password": "Admin@123"})
    assert res_b.status_code == 200
    token_b = res_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Clinic B queries batches -> Must be isolated, cannot see Clinic A's batches
    res_batches_b = client.get("/api/pharmacy/batches", headers=headers_b)
    assert res_batches_b.status_code == 200
    batches_b = res_batches_b.json()["data"]
    batch_nums_b = [b["batch_number"] for b in batches_b]
    assert "AZT2026B1" not in batch_nums_b
    assert "PARA26V" not in batch_nums_b

    # Clinic B queries transactions -> Cannot see Clinic A's transactions
    res_tx_b = client.get("/api/pharmacy/transactions", headers=headers_b)
    assert res_tx_b.status_code == 200
    assert len(res_tx_b.json()["data"]) == 0
