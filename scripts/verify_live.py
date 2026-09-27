import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app

def run_verification():
    print("=== CarePulse Hospital AI Automation Live Verification ===")
    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    print(f"[PASS] Health: {res.json()['status']}, DB: {res.json()['database']}")

    # 2. Patient Auth
    res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert res.status_code == 200
    p_token = res.json()["data"]["access_token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}
    print("[PASS] Patient authenticated.")

    # 3. Doctors & Slots
    res = client.get("/api/doctors")
    assert res.status_code == 200
    doctors = res.json()["data"]
    doc = doctors[0]
    
    # Find next available working day
    test_date = None
    slots = []
    for day_offset in range(1, 8):
        candidate_date = (date.today() + timedelta(days=day_offset)).isoformat()
        res = client.get(f"/api/doctors/{doc['id']}/slots?date={candidate_date}")
        if res.status_code == 200:
            avail = [s for s in res.json()["data"] if not s["is_booked"]]
            if avail:
                test_date = candidate_date
                slots = avail
                break

    assert test_date is not None and len(slots) > 0
    print(f"[PASS] Found {len(doctors)} doctors. {len(slots)} available slots for Dr. {doc['full_name']} on {test_date}.")

    # 4. Book Appointment
    slot_time = slots[0]["start_time"]
    res = client.post("/api/appointments", json={
        "doctor_id": doc["id"],
        "appointment_date": test_date,
        "appointment_time": slot_time,
        "reason": "Routine hypertension checkup"
    }, headers=p_headers)
    assert res.status_code == 201
    appt = res.json()["data"]
    print(f"[PASS] Booked appointment: {appt['id']} (Status: {appt['status']})")

    # 5. AI Chat & Guardrails
    res = client.post("/api/ai/chat", json={"message": "tell me about cetirizine"}, headers=p_headers)
    assert res.status_code == 200
    assert "Cetirizine" in res.json()["data"]["response"]
    print(f"[PASS] AI Medication Info: {res.json()['data']['response'][:55]}...")

    res = client.post("/api/ai/chat", json={"message": "Can I check my reports and doctors?"}, headers=p_headers)
    assert res.status_code == 200
    print(f"[PASS] AI Chat Reply: {res.json()['data']['response'][:50]}...")

    res = client.post("/api/ai/chat", json={"message": "I have severe sudden chest pain and shortness of breath"}, headers=p_headers)
    assert res.status_code == 200
    assert res.json()["data"]["is_emergency"] is True
    print("[PASS] Emergency guardrail triggered & auto-escalated.")

    # 6. Reports & Feedback
    res = client.get("/api/reports/my", headers=p_headers)
    assert res.status_code == 200
    res = client.post("/api/feedback", json={"rating": 5, "comment": "Great care!"}, headers=p_headers)
    assert res.status_code == 201
    print("[PASS] Reports and feedback verified.")

    # 7. Doctor Portal
    res = client.post("/api/auth/login", json={"email": "dr.sharma@hospital.com", "password": "Doctor@123"})
    assert res.status_code == 200
    d_token = res.json()["data"]["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}
    res = client.get("/api/doctor/appointments", headers=d_headers)
    assert res.status_code == 200
    print(f"[PASS] Doctor portal: {len(res.json()['data'])} appointments listed.")

    # 8. Admin Operations
    res = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert res.status_code == 200
    a_token = res.json()["data"]["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}
    res = client.get("/api/admin/stats", headers=a_headers)
    assert res.status_code == 200
    print(f"[PASS] Admin stats: {res.json()['data']['metrics']}")

    print("=== ALL LIVE VERIFICATION CHECKS PASSED ===")

if __name__ == "__main__":
    run_verification()
