import pytest
from datetime import date, timedelta


def test_complete_hospital_workflow(client, seed_test_data):
    # 1. Login as patient
    login_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get doctors
    docs_res = client.get("/api/doctors")
    assert docs_res.status_code == 200
    docs = docs_res.json()["data"]
    assert len(docs) >= 1
    doc_id = docs[0]["id"]

    # 3. Check slots for tomorrow
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    slots_res = client.get(f"/api/doctors/{doc_id}/slots?date={tomorrow}")
    assert slots_res.status_code == 200
    slots_data = slots_res.json()["data"]
    assert len(slots_data) > 0
    available_slots = [s for s in slots_data if not s["is_booked"]]
    assert len(available_slots) >= 2
    slot_time = available_slots[0]["start_time"]
    next_slot = available_slots[1]["start_time"]

    # 4. Book appointment
    book_payload = {
        "doctor_id": doc_id,
        "appointment_date": tomorrow,
        "appointment_time": slot_time,
        "reason": "Chest checkup",
    }
    book_res = client.post("/api/appointments", json=book_payload, headers=headers)
    assert book_res.status_code == 201
    appt = book_res.json()["data"]
    appt_id = appt["id"]
    assert appt["status"] == "confirmed"

    # 5. Get My Appointments
    my_appts = client.get("/api/appointments/my", headers=headers)
    assert my_appts.status_code == 200
    assert len(my_appts.json()["data"]) >= 1

    # 6. Reschedule appointment
    resched_res = client.patch(
        f"/api/appointments/{appt_id}/reschedule",
        json={"new_date": tomorrow, "new_time": next_slot, "reason": "Conflict with schedule"},
        headers=headers,
    )
    assert resched_res.status_code == 200
    assert resched_res.json()["data"]["appointment_time"] == next_slot

    # 7. Cancel appointment
    cancel_res = client.patch(
        f"/api/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Feeling better"},
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"

    # 8. Request Voice Call
    voice_res = client.post(
        "/api/voice/request",
        json={"reason": "Need urgent doctor confirmation"},
        headers=headers,
    )
    assert voice_res.status_code == 201
    assert voice_res.json()["data"]["status"] == "requested"

    # 9. Create Escalation
    esc_res = client.post(
        "/api/escalations",
        json={"reason": "billing", "message": "Need clarification on invoice details", "priority": "medium"},
        headers=headers,
    )
    assert esc_res.status_code == 201
    assert esc_res.json()["data"]["status"] == "open"

    # 10. Submit Patient Feedback
    feedback_res = client.post(
        "/api/feedback",
        json={"rating": 5, "comment": "Excellent clinic care and responsive AI bot!"},
        headers=headers,
    )
    assert feedback_res.status_code == 201
    assert feedback_res.json()["data"]["rating"] == 5

    # 11. View Patient Reports
    reports_res = client.get("/api/reports/my", headers=headers)
    assert reports_res.status_code == 200
    assert isinstance(reports_res.json()["data"], list)

    # 12. Doctor Login and Portal
    doc_login = client.post("/api/auth/login", json={"email": "doctor@hospital.com", "password": "Doctor@123"})
    assert doc_login.status_code == 200
    doc_token = doc_login.json()["data"]["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    doc_appts = client.get("/api/doctor/appointments", headers=doc_headers)
    assert doc_appts.status_code == 200
    assert isinstance(doc_appts.json()["data"], list)

    if doc_appts.json()["data"]:
        test_appt_id = doc_appts.json()["data"][0]["id"]
        doc_update = client.patch(
            f"/api/doctor/appointments/{test_appt_id}/status",
            json={"status": "completed", "notes": "Completed consultation notes."},
            headers=doc_headers,
        )
        assert doc_update.status_code == 200
        assert doc_update.json()["data"]["status"] == "completed"

    # 13. RBAC Check: Patient forbidden from admin routes
    rbac_res = client.get("/api/admin/stats", headers=headers)
    assert rbac_res.status_code == 403

    # 14. Login as Admin and view dashboard stats, escalations, feedback, error logs
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    dash_res = client.get("/api/admin/stats", headers=admin_headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["data"]["metrics"]["total_doctors"] >= 1

    admin_appt_update = client.patch(
        f"/api/admin/appointments/{appt_id}/status",
        json={"status": "confirmed", "notes": "Confirmed by admin desk."},
        headers=admin_headers,
    )
    assert admin_appt_update.status_code == 200

    escalations_res = client.get("/api/admin/escalations", headers=admin_headers)
    assert escalations_res.status_code == 200
    assert len(escalations_res.json()["data"]) >= 1

    admin_feedback = client.get("/api/admin/feedback", headers=admin_headers)
    assert admin_feedback.status_code == 200
    assert len(admin_feedback.json()["data"]) >= 1

    admin_errors = client.get("/api/admin/errors", headers=admin_headers)
    assert admin_errors.status_code == 200
    assert isinstance(admin_errors.json()["data"], list)


