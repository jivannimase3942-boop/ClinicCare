import pytest


def test_reports_workflow(client, seed_test_data):
    # Admin logs in to create report
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_rep = client.post(
        "/api/admin/reports",
        json={
            "patient_id": seed_test_data["patient"].id,
            "doctor_id": seed_test_data["doctor"].id,
            "title": "Lipid Profile & ECG",
            "report_type": "Pathology",
            "status": "ready",
            "summary": "Normal cholesterol levels, clear ECG waveform.",
        },
        headers=admin_headers,
    )
    assert create_rep.status_code == 201
    rep_id = create_rep.json()["data"]["id"]

    # Patient checks their reports
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    my_reps = client.get("/api/reports/my", headers=pat_headers)
    assert my_reps.status_code == 200
    reports = my_reps.json()["data"]
    assert len(reports) >= 1
    assert reports[0]["title"] == "Lipid Profile & ECG"

    # Patient views specific report
    one_rep = client.get(f"/api/reports/{rep_id}", headers=pat_headers)
    assert one_rep.status_code == 200
    assert one_rep.json()["data"]["summary"] == "Normal cholesterol levels, clear ECG waveform."


def test_feedback_and_voice_workflows(client, seed_test_data):
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # Submit feedback
    fb_res = client.post(
        "/api/feedback",
        json={"rating": 5, "comment": "Excellent treatment and prompt service!"},
        headers=pat_headers,
    )
    assert fb_res.status_code == 201
    assert fb_res.json()["data"]["rating"] == 5

    # Get my feedback
    my_fb = client.get("/api/feedback/my", headers=pat_headers)
    assert my_fb.status_code == 200
    assert len(my_fb.json()["data"]) >= 1

    # Request voice call
    voice_res = client.post(
        "/api/voice/request",
        json={"phone": "+1555987654", "reason": "Follow-up question on prescribed pills"},
        headers=pat_headers,
    )
    assert voice_res.status_code == 201
    assert voice_res.json()["data"]["status"] == "requested"

    # Get my voice requests
    my_voice = client.get("/api/voice/my", headers=pat_headers)
    assert my_voice.status_code == 200
    assert len(my_voice.json()["data"]) >= 1


def test_escalation_workflow(client, seed_test_data):
    # Patient triggers escalation
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    esc_res = client.post(
        "/api/escalations",
        json={"reason": "emergency", "message": "High fever with sudden rashes", "priority": "high"},
        headers=pat_headers,
    )
    assert esc_res.status_code == 201
    esc_id = esc_res.json()["data"]["id"]

    # Admin checks and resolves escalation
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    escs = client.get("/api/admin/escalations", headers=admin_headers)
    assert escs.status_code == 200
    assert len(escs.json()["data"]) >= 1

    resolve_res = client.patch(
        f"/api/admin/escalations/{esc_id}",
        json={"status": "resolved", "admin_notes": "Triage nurse contacted the patient immediately."},
        headers=admin_headers,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["data"]["status"] == "resolved"

