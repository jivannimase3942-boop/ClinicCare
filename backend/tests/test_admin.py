import pytest
from datetime import date, timedelta


def test_admin_full_management(client, seed_test_data):
    # 1. Login as Admin
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    assert admin_login.status_code == 200
    token = admin_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create department
    dept_res = client.post(
        "/api/admin/departments",
        json={"name": "Dermatology", "description": "Skin and aesthetic care unit", "icon": "Sparkles"},
        headers=headers,
    )
    assert dept_res.status_code == 201
    assert dept_res.json()["data"]["name"] == "Dermatology"

    # 3. Create Diagnostic Report for Patient
    patient = seed_test_data["patient"]
    doctor = seed_test_data["doctor"]

    rep_res = client.post(
        "/api/admin/reports",
        json={
            "patient_id": patient.id,
            "doctor_id": doctor.id,
            "title": "Comprehensive Metabolic Panel",
            "report_type": "blood_test",
            "summary": "All metabolic biomarkers are in standard ranges.",
            "status": "ready"
        },
        headers=headers,
    )
    assert rep_res.status_code == 201
    rep_id = rep_res.json()["data"]["id"]
    assert rep_res.json()["data"]["status"] == "ready"

    # 4. Update Diagnostic Report status
    update_rep = client.patch(
        f"/api/admin/reports/{rep_id}/status",
        json={"status": "delivered"},
        headers=headers,
    )
    assert update_rep.status_code == 200
    assert update_rep.json()["data"]["status"] == "delivered"

    # 5. Get and Update Voice Calls
    # First create voice call as patient
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    voice_req = client.post("/api/voice/request", json={"phone": "+15550199", "reason": "Followup on lab test"}, headers=pat_headers)
    assert voice_req.status_code == 201
    call_id = voice_req.json()["data"]["id"]

    # Admin updates voice call status
    call_update = client.patch(
        f"/api/admin/voice-calls/{call_id}",
        json={"status": "completed", "notes": "Called patient and clarified lab parameters."},
        headers=headers,
    )
    assert call_update.status_code == 200
    assert call_update.json()["data"]["status"] == "completed"

    # 6. Admin resolves escalation
    esc_req = client.post("/api/escalations", json={"reason": "medical_question", "message": "High dosage concern", "priority": "high"}, headers=pat_headers)
    assert esc_req.status_code == 201
    esc_id = esc_req.json()["data"]["id"]

    esc_resolve = client.patch(
        f"/api/admin/escalations/{esc_id}",
        json={"status": "resolved", "admin_notes": "Prescription reviewed and confirmed safe."},
        headers=headers,
    )
    assert esc_resolve.status_code == 200
    assert esc_resolve.json()["data"]["status"] == "resolved"
