from datetime import date, timedelta


def test_doctor_slots_and_booking_flow(client, seed_test_data):
    doc_id = seed_test_data["doctor"].id
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # 1. Check doctor slots
    slots_resp = client.get(f"/api/doctors/{doc_id}/slots?date={tomorrow}")
    assert slots_resp.status_code == 200
    slots = slots_resp.json()["data"]
    assert len(slots) > 0

    # 2. Login as patient
    login_resp = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Book appointment
    book_payload = {
        "doctor_id": doc_id,
        "appointment_date": tomorrow,
        "appointment_time": "10:00",
        "reason": "Chest checkup",
        "notes": "First visit"
    }
    book_resp = client.post("/api/appointments", json=book_payload, headers=headers)
    assert book_resp.status_code == 201
    app_data = book_resp.json()["data"]
    app_id = app_data["id"]
    assert app_data["status"] == "confirmed"

    # 4. Double booking should fail
    dup_resp = client.post("/api/appointments", json=book_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 5. List patient appointments
    my_apps_resp = client.get("/api/appointments/my", headers=headers)
    assert my_apps_resp.status_code == 200
    my_apps = my_apps_resp.json()["data"]
    assert len(my_apps) == 1
    assert my_apps[0]["id"] == app_id

    # 6. Reschedule appointment
    day_after = (date.today() + timedelta(days=2)).isoformat()
    reschedule_payload = {
        "new_date": day_after,
        "new_time": "11:00",
        "reason": "Schedule conflict"
    }
    resched_resp = client.patch(f"/api/appointments/{app_id}/reschedule", json=reschedule_payload, headers=headers)
    assert resched_resp.status_code == 200
    assert resched_resp.json()["data"]["appointment_time"] == "11:00"

    # 7. Cancel appointment
    cancel_resp = client.patch(f"/api/appointments/{app_id}/cancel", json={"cancelled_reason": "Feeling better"}, headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "cancelled"
