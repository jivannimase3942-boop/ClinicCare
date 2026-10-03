import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.clinic import Clinic
from app.models.user import User, Patient, Doctor
from app.models.billing import Invoice, Payment, Refund


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def auth_tokens(client):
    admin_res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_res.json()["data"]["access_token"]

    fd_res = client.post("/api/auth/login", json={"email": "frontdesk@hospital.com", "password": "FrontDesk@123"})
    fd_token = fd_res.json()["data"]["access_token"]

    pat_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_res.json()["data"]["access_token"]

    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "frontdesk": {"Authorization": f"Bearer {fd_token}"},
        "patient": {"Authorization": f"Bearer {pat_token}"},
    }


def test_invoice_creation_and_payment_flow(client, db_session, auth_tokens):
    # Find patient
    patient = db_session.query(Patient).first()
    assert patient is not None

    # 1. Front desk creates invoice
    invoice_payload = {
        "patient_id": patient.id,
        "items": [
            {
                "item_type": "CONSULTATION",
                "description": "General OPD Consultation",
                "quantity": 1,
                "unit_price": 500.00
            },
            {
                "item_type": "PROCEDURE",
                "description": "ECG Recording & Report",
                "quantity": 1,
                "unit_price": 300.00
            }
        ],
        "discount_amount": 50.00,
        "tax_rate_percent": 5.0,  # 5% tax on (800 - 50) = 750 * 0.05 = 37.50 => total 787.50
        "notes": "First visit checkup invoice"
    }

    inv_res = client.post("/api/billing/invoices", json=invoice_payload, headers=auth_tokens["frontdesk"])
    assert inv_res.status_code == 201
    inv_data = inv_res.json()["data"]
    inv_id = inv_data["id"]

    assert inv_data["subtotal"] == 800.00
    assert inv_data["discount_amount"] == 50.00
    assert inv_data["tax_amount"] == 37.50
    assert inv_data["total_amount"] == 787.50
    assert inv_data["balance_due"] == 787.50
    assert inv_data["status"] == "PENDING"
    assert inv_data["invoice_number"].startswith("INV-")

    # 2. Patient cannot create an invoice (must be 403)
    unauth_create = client.post("/api/billing/invoices", json=invoice_payload, headers=auth_tokens["patient"])
    assert unauth_create.status_code == 403

    # 3. Record partial payment (e.g. 500.00 via UPI)
    pay_res = client.post(f"/api/billing/invoices/{inv_id}/payments", json={
        "amount": 500.00,
        "payment_method": "UPI",
        "transaction_reference": "UPI/12345678/REF",
        "notes": "Paid via Google Pay"
    }, headers=auth_tokens["frontdesk"])
    assert pay_res.status_code == 200
    updated_inv = pay_res.json()["data"]
    assert updated_inv["amount_paid"] == 500.00
    assert updated_inv["balance_due"] == 287.50
    assert updated_inv["status"] == "PARTIALLY_PAID"
    assert len(updated_inv["payments"]) == 1

    # 4. Record remaining payment (287.50 via CASH)
    pay_res_2 = client.post(f"/api/billing/invoices/{inv_id}/payments", json={
        "amount": 287.50,
        "payment_method": "CASH",
        "notes": "Paid in cash"
    }, headers=auth_tokens["frontdesk"])
    assert pay_res_2.status_code == 200
    final_inv = pay_res_2.json()["data"]
    assert final_inv["amount_paid"] == 787.50
    assert final_inv["balance_due"] == 0.00
    assert final_inv["status"] == "PAID"
    assert len(final_inv["payments"]) == 2

    # 5. Process partial refund by Admin (e.g. 100.00)
    refund_res = client.post(f"/api/billing/invoices/{inv_id}/refund", json={
        "amount": 100.00,
        "reason": "Adjustment for discounted lab service"
    }, headers=auth_tokens["admin"])
    assert refund_res.status_code == 200
    refunded_inv = refund_res.json()["data"]
    assert refunded_inv["amount_paid"] == 687.50
    assert refunded_inv["balance_due"] == 100.00
    assert refunded_inv["status"] == "PARTIALLY_PAID"

    # Front Desk cannot process refunds (restricted to ADMIN)
    fd_refund = client.post(f"/api/billing/invoices/{inv_id}/refund", json={
        "amount": 50.00,
        "reason": "Test"
    }, headers=auth_tokens["frontdesk"])
    assert fd_refund.status_code == 403


def test_billing_tenant_isolation_and_privacy(client, db_session, auth_tokens):
    # 1. Onboard a secondary clinic
    ts = int(time.time())
    onboard_res = client.post("/api/clinics/onboard", json={
        "name": f"Metro Care Clinic {ts}",
        "slug": f"metro-care-{ts}",
        "phone": "+91 99887 76655",
        "email": f"billing-{ts}@metrocare.in",
        "address": "MG Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
        "country": "India",
        "operating_hours": "09:00 - 18:00",
        "consultation_fee_default": 500.00,
        "departments": ["General Medicine"],
        "services": ["OPD Consultation"],
        "admin_name": f"Metro Admin {ts}",
        "admin_email": f"metro_admin_{ts}@metrocare.in",
        "admin_password": "SecurePassword@123",
        "admin_phone": "+91 99887 76656",
        "doctor_name": f"Dr. Metro {ts}",
        "doctor_email": f"metro_doc_{ts}@metrocare.in",
        "doctor_specialization": "General Physician",
        "doctor_qualification": "MBBS",
        "doctor_fee": 500.00,
    })
    assert onboard_res.status_code == 201
    clinic_b_id = onboard_res.json()["data"]["clinic"]["id"]
    clinic_b_admin_email = onboard_res.json()["data"]["admin_user"]["email"]

    # Login as Clinic B Admin
    b_login = client.post("/api/auth/login", json={"email": clinic_b_admin_email, "password": "SecurePassword@123"})
    assert b_login.status_code == 200
    b_token = b_login.json()["data"]["access_token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    # Find patient
    patient = db_session.query(Patient).first()

    # Clinic B creates an invoice for Clinic B
    inv_b = client.post("/api/billing/invoices", json={
        "patient_id": patient.id,
        "items": [{"item_type": "CONSULTATION", "description": "Consult", "quantity": 1, "unit_price": 500.0}],
    }, headers=b_headers)
    assert inv_b.status_code == 201
    b_invoice_id = inv_b.json()["data"]["id"]

    # Clinic A frontdesk attempts to access Clinic B's invoice -> MUST RETURN 403
    cross_access = client.get(f"/api/billing/invoices/{b_invoice_id}", headers=auth_tokens["frontdesk"])
    assert cross_access.status_code == 403, f"Expected 403 cross-tenant block, got {cross_access.status_code}"


def test_online_payment_readiness_no_fake_success(client, auth_tokens, db_session):
    # Get any invoice
    inv = db_session.query(Invoice).first()
    assert inv is not None

    res = client.post(f"/api/billing/online-order?invoice_id={inv.id}", headers=auth_tokens["frontdesk"])
    assert res.status_code == 200
    data = res.json()
    # Confirms it never claims payment was made when credentials not configured
    assert data["success"] is False
    assert "not configured" in data["message"].lower()
    assert data["data"]["gateway_configured"] is False
