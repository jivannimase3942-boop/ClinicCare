import pytest
import time
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, Doctor, Patient
from app.models.appointment import Appointment, DoctorSlot, DoctorLeave, AppointmentWaitlist


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
def tokens(client):
    # Admin
    admin_res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_res.json()["data"]["access_token"]

    # Doctor
    doc_res = client.post("/api/auth/login", json={"email": "dr.sharma@hospital.com", "password": "Doctor@123"})
    doc_token = doc_res.json()["data"]["access_token"]

    # Front Desk
    fd_res = client.post("/api/auth/login", json={"email": "frontdesk@hospital.com", "password": "FrontDesk@123"})
    fd_token = fd_res.json()["data"]["access_token"]

    # Patient
    pat_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_res.json()["data"]["access_token"]

    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "doctor": {"Authorization": f"Bearer {doc_token}"},
        "frontdesk": {"Authorization": f"Bearer {fd_token}"},
        "patient": {"Authorization": f"Bearer {pat_token}"},
    }


def test_doctor_leave_and_break_slots(client, db_session, tokens):
    doc = db_session.query(Doctor).filter(Doctor.is_active == True).first()
    assert doc is not None

    tomorrow = date.today() + timedelta(days=2)
    # Check slots before leave
    res_before = client.get(f"/api/doctors/{doc.id}/slots?date={tomorrow.isoformat()}", headers=tokens["doctor"])
    assert res_before.status_code == 200
    slots_before = res_before.json()["data"]

    # Verify break period 13:00 to 14:00 is excluded
    for s in slots_before:
        assert not ("13:00" <= s["start_time"] < "14:00"), f"Slot {s['start_time']} should not be in break period"

    # Add doctor leave for tomorrow
    leave_payload = {
        "doctor_id": doc.id,
        "start_date": tomorrow.isoformat(),
        "end_date": tomorrow.isoformat(),
        "reason": "Cardiology Conference"
    }
    leave_res = client.post(f"/api/doctors/{doc.id}/leaves", json=leave_payload, headers=tokens["doctor"])
    assert leave_res.status_code == 201
    assert leave_res.json()["data"]["reason"] == "Cardiology Conference"

    # Request slots on leave date - must return 0 slots
    res_after = client.get(f"/api/doctors/{doc.id}/slots?date={tomorrow.isoformat()}", headers=tokens["doctor"])
    assert res_after.status_code == 200
    assert len(res_after.json()["data"]) == 0

    # Attempt to book appointment on leave date - must fail
    book_fail = client.post("/api/appointments", json={
        "doctor_id": doc.id,
        "appointment_date": tomorrow.isoformat(),
        "appointment_time": "10:00",
        "reason": "Checkup"
    }, headers=tokens["patient"])
    assert book_fail.status_code == 400
    assert "leave" in book_fail.json()["detail"].lower()


def test_double_booking_prevention(client, db_session, tokens):
    doc = db_session.query(Doctor).filter(Doctor.is_active == True).first()
    target_date = date.today() + timedelta(days=30 + (int(time.time() * 7) % 300))

    # 1. Book first appointment
    first_book = client.post("/api/appointments", json={
        "doctor_id": doc.id,
        "appointment_date": target_date.isoformat(),
        "appointment_time": "11:00",
        "reason": "First booking",
        "appointment_type": "NEW_CONSULTATION"
    }, headers=tokens["patient"])
    assert first_book.status_code == 201

    # 2. Attempt duplicate booking for same doctor, date and time
    duplicate_book = client.post("/api/appointments", json={
        "doctor_id": doc.id,
        "appointment_date": target_date.isoformat(),
        "appointment_time": "11:00",
        "reason": "Duplicate attempt",
        "appointment_type": "NEW_CONSULTATION"
    }, headers=tokens["patient"])
    assert duplicate_book.status_code == 400
    assert "already booked" in duplicate_book.json()["detail"].lower()


def test_walk_in_and_queue_workflow(client, db_session, tokens):
    doc = db_session.query(Doctor).filter(Doctor.is_active == True).first()

    # 1. Create walk-in appointment from frontdesk
    ts = int(time.time())
    walkin_res = client.post("/api/appointments/walk-in", json={
        "doctor_id": doc.id,
        "patient_name": f"Walkin Patient {ts}",
        "patient_phone": f"+9198765{ts % 100000:05d}",
        "reason": "Acute Cough and Mild Fever",
        "appointment_type": "NEW_CONSULTATION"
    }, headers=tokens["frontdesk"])

    assert walkin_res.status_code == 201
    walkin_data = walkin_res.json()["data"]
    app_id = walkin_data["id"]
    assert walkin_data["is_walk_in"] is True
    assert walkin_data["token_number"] is not None
    assert walkin_data["queue_status"] == "WAITING"
    assert walkin_data["status"] == "checked_in"

    # 2. Check today's queue
    queue_res = client.get("/api/appointments/queue/today", headers=tokens["frontdesk"])
    assert queue_res.status_code == 200
    queue_items = queue_res.json()["data"]
    assert any(q["id"] == app_id for q in queue_items)

    # 3. Doctor calls the patient
    call_res = client.patch(f"/api/appointments/{app_id}/queue", json={
        "queue_status": "CALLED",
        "notes": "Patient called to Room 1"
    }, headers=tokens["doctor"])
    assert call_res.status_code == 200
    assert call_res.json()["data"]["queue_status"] == "CALLED"

    # 4. Doctor starts consultation
    consult_res = client.patch(f"/api/appointments/{app_id}/queue", json={
        "queue_status": "IN_CONSULTATION"
    }, headers=tokens["doctor"])
    assert consult_res.status_code == 200
    assert consult_res.json()["data"]["queue_status"] == "IN_CONSULTATION"
    assert consult_res.json()["data"]["status"] == "in_consultation"

    # 5. Doctor completes consultation
    done_res = client.patch(f"/api/appointments/{app_id}/queue", json={
        "queue_status": "COMPLETED"
    }, headers=tokens["doctor"])
    assert done_res.status_code == 200
    assert done_res.json()["data"]["queue_status"] == "COMPLETED"
    assert done_res.json()["data"]["status"] == "completed"


def test_waitlist_and_conversion(client, db_session, tokens):
    doc = db_session.query(Doctor).filter(Doctor.is_active == True).first()
    future_date = date.today() + timedelta(days=60 + (int(time.time() * 11) % 300))

    # 1. Patient joins waitlist
    wl_res = client.post("/api/appointments/waitlist", json={
        "doctor_id": doc.id,
        "desired_date": future_date.isoformat(),
        "preferred_time_range": "Morning",
        "notes": "Urgent review if slot opens"
    }, headers=tokens["patient"])
    assert wl_res.status_code == 201
    wl_data = wl_res.json()["data"]
    wl_id = wl_data["id"]
    assert wl_data["status"] == "WAITING"

    # 2. Front desk lists waitlist
    list_res = client.get(f"/api/appointments/waitlist?doctor_id={doc.id}", headers=tokens["frontdesk"])
    assert list_res.status_code == 200
    assert any(w["id"] == wl_id for w in list_res.json()["data"])

    # 3. Front desk converts waitlist to booked appointment
    convert_res = client.post(f"/api/appointments/waitlist/{wl_id}/convert?appointment_time=09:30", headers=tokens["frontdesk"])
    assert convert_res.status_code == 200
    converted_app = convert_res.json()["data"]
    assert converted_app["appointment_time"] == "09:30"
    assert converted_app["status"] == "confirmed"
