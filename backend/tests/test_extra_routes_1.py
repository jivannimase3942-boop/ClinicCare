import pytest


def test_departments_and_doctors_listing(client, seed_test_data):
    # Test get departments
    res = client.get("/api/departments")
    assert res.status_code == 200
    depts = res.json()["data"]
    assert len(depts) >= 1
    assert depts[0]["name"] == "Cardiology"

    # Test get doctors in department
    dept_id = seed_test_data["dept"].id
    res = client.get(f"/api/doctors?department_id={dept_id}")
    assert res.status_code == 200
    docs = res.json()["data"]
    assert len(docs) >= 1
    assert docs[0]["specialization"] == "Cardiologist"


def test_doctor_portal_workflow(client, seed_test_data):
    # Doctor login
    login_res = client.post("/api/auth/login", json={"email": "doctor@hospital.com", "password": "Doctor@123"})
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Patient books appointment
    pat_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_res.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    book_res = client.post(
        "/api/appointments",
        json={
            "doctor_id": seed_test_data["doctor"].id,
            "appointment_date": "2026-10-15",
            "appointment_time": "10:00",
            "reason": "Chest tightness",
        },
        headers=pat_headers,
    )
    assert book_res.status_code == 201
    appt_id = book_res.json()["data"]["id"]

    # Doctor views their consultations
    doc_appts = client.get("/api/doctor/appointments", headers=headers)
    assert doc_appts.status_code == 200
    appts = doc_appts.json()["data"]
    assert len(appts) >= 1

    # Doctor updates status to completed
    update_res = client.patch(
        f"/api/doctor/appointments/{appt_id}/status",
        json={"status": "completed"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "completed"


def test_password_change_flow(client, seed_test_data):
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # Change password
    chg_res = client.patch(
        "/api/auth/change-password",
        json={"current_password": "Patient@123", "new_password": "NewSecretPassword@123"},
        headers=pat_headers,
    )
    assert chg_res.status_code == 200

    # Old password fails
    fail_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    assert fail_res.status_code == 401

    # New password succeeds
    ok_res = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "NewSecretPassword@123"})
    assert ok_res.status_code == 200
