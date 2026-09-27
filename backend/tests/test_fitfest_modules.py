from datetime import date, datetime, timedelta
import pytest


def get_tokens(client):
    admin_login = client.post("/api/auth/login", json={"email": "admin@hospital.com", "password": "Admin@123"})
    admin_token = admin_login.json()["data"]["access_token"]
    pat_login = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    pat_token = pat_login.json()["data"]["access_token"]
    return admin_token, pat_token


def test_fitfest_ambulances_flow(client, seed_test_data):
    """Test ambulance list, request, assignment, and status transition."""
    admin_token, _ = get_tokens(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. List ambulances
    resp = client.get("/api/ambulances")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1

    # 2. Patient requests ambulance
    req_payload = {
        "requester_name": "Emergency Caller",
        "requester_phone": "+1 (800) 555-0911",
        "pickup_address": "42 Emergency Way, Metropolis",
        "destination_facility": "ClinicCare Multispeciality Hospital",
        "emergency_priority": "critical",
        "notes": "Severe allergic reaction and breathing distress"
    }
    req_resp = client.post("/api/ambulances/request", json=req_payload)
    assert req_resp.status_code == 201
    req_data = req_resp.json()["data"]
    assert req_data["requester_name"] == "Emergency Caller"
    assert req_data["status"] in ["assigned", "requested"]

    # 3. List requests
    list_resp = client.get("/api/ambulances/requests")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 4. Update status
    upd_resp = client.patch(
        f"/api/ambulances/requests/{req_data['id']}",
        json={"status": "completed", "notes": "Patient delivered to emergency ER room safely"},
        headers=headers
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["data"]["status"] == "completed"


def test_fitfest_blood_bank_flow(client, seed_test_data):
    """Test blood banks listing, blood group search, and blood requirement requests."""
    admin_token, pat_token = get_tokens(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # 1. List banks
    resp = client.get("/api/blood/banks")
    assert resp.status_code == 200
    banks = resp.json()["data"]
    assert len(banks) >= 1
    bank_id = banks[0]["id"]

    # 2. Search blood group O+
    search_resp = client.get("/api/blood/search?blood_group=O%2B")
    assert search_resp.status_code == 200
    results = search_resp.json()["data"]
    assert len(results) >= 1
    assert results[0]["blood_group"] == "O+"

    # 3. Search blood group A+
    a_resp = client.get("/api/blood/search?blood_group=A%2B")
    assert a_resp.status_code == 200
    assert len(a_resp.json()["data"]) >= 1

    # 4. Patient creates blood requirement request
    req_payload = {
        "patient_name": "Emergency Patient",
        "blood_group": "B+",
        "units_required": 2,
        "hospital_clinic_name": "ClinicCare Main Hospital",
        "location": "Trauma Ward 2",
        "contact_phone": "+1 (800) 555-0999",
        "urgency": "urgent",
        "additional_info": "Urgent surgery replacement."
    }
    create_req_resp = client.post("/api/blood/requests", json=req_payload, headers=pat_headers)
    assert create_req_resp.status_code == 201
    req_data = create_req_resp.json()["data"]
    req_id = req_data["id"]
    assert req_data["blood_group"] == "B+"
    assert req_data["status"] == "submitted"

    # 5. List blood requests
    list_req_resp = client.get("/api/blood/requests")
    assert list_req_resp.status_code == 200
    assert len(list_req_resp.json()["data"]) >= 1

    # 6. Admin matches blood bank to request
    match_resp = client.post(
        f"/api/blood/requests/{req_id}/match",
        json={"blood_bank_id": bank_id, "notes": "Units reserved at central blood bank"},
        headers=headers
    )
    assert match_resp.status_code == 200
    assert match_resp.json()["data"]["status"] == "match_found"
    assert match_resp.json()["data"]["matched_blood_bank_id"] == bank_id

    # 7. Admin updates request to fulfilled
    upd_resp = client.patch(
        f"/api/blood/requests/{req_id}",
        json={"status": "fulfilled", "admin_notes": "Delivered to ICU"},
        headers=headers
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["data"]["status"] == "fulfilled"


def test_fitfest_facilities_flow(client, seed_test_data):
    """Test facilities directory endpoint."""
    resp = client.get("/api/facilities")
    assert resp.status_code == 200
    facs = resp.json()["data"]
    assert len(facs) >= 1
    assert any("ClinicCare" in f["name"] for f in facs)




def test_fitfest_patient_search_and_visits(client, seed_test_data):
    """Test patient search by name and visit history."""
    admin_token, _ = get_tokens(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    pat = seed_test_data["patient"]
    pat_user = seed_test_data["patient_user"]

    # 1. Search by name
    resp = client.get(f"/api/patients?search={pat_user.full_name[:4]}")
    assert resp.status_code == 200
    results = resp.json()["data"]
    assert len(results) >= 1

    # 2. Get patient visits
    v_resp = client.get(f"/api/patients/{pat.id}/visits")
    assert v_resp.status_code == 200

    # 3. Record visit
    doc = seed_test_data["doctor"]
    rec_resp = client.post(
        f"/api/patients/{pat.id}/visits",
        json={
            "patient_id": pat.id,
            "doctor_id": doc.id,
            "visit_date": date.today().isoformat(),
            "visit_type": "OPD Consultation",
            "vitals_summary": "BP: 120/80 mmHg | SpO2: 99%",
            "administrative_notes": "Routine checkup completed.",
            "follow_up_instructions": "Visit again in 6 months."
        },
        headers=headers
    )
    assert rec_resp.status_code == 201
    assert rec_resp.json()["data"]["visit_type"] == "OPD Consultation"


def test_fitfest_emergencies_and_reminders(client, seed_test_data):
    """Test emergency stats, creation and follow-up reminders."""
    admin_token, _ = get_tokens(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    pat = seed_test_data["patient"]

    # 1. Emergency stats
    stats_resp = client.get("/api/emergencies/stats")
    assert stats_resp.status_code == 200
    assert "total_emergencies" in stats_resp.json()["data"]

    # 2. Create emergency request
    em_resp = client.post(
        "/api/emergencies",
        json={
            "patient_id": pat.id,
            "caller_name": "Emergency Witness",
            "caller_phone": "+1 (800) 555-0999",
            "location": "Central Square, Sector 4",
            "emergency_type": "Cardiac Alert",
            "priority": "critical",
            "requires_ambulance": True,
            "notes": "Patient collapsed on street, CPR initiated."
        }
    )
    assert em_resp.status_code == 201
    assert em_resp.json()["data"]["priority"] in ["emergency", "critical"]

    # 3. List reminders
    rem_resp = client.get("/api/reminders")
    assert rem_resp.status_code == 200

    # 4. Schedule reminder
    sch_resp = client.post(
        "/api/reminders",
        json={
            "patient_id": pat.id,
            "title": "Post-discharge follow-up reminder",
            "message": "Please remember to monitor your blood pressure daily.",
            "scheduled_for": (datetime.now() + timedelta(days=2)).isoformat(),
            "channel": "WhatsApp/SMS (Demo)"
        },
        headers=headers
    )
    assert sch_resp.status_code == 201
    rem_id = sch_resp.json()["data"]["id"]

    # 5. Dispatch reminder
    disp_resp = client.post(f"/api/reminders/{rem_id}/dispatch")
    assert disp_resp.status_code == 200
    assert disp_resp.json()["data"]["status"] == "sent_demo"


def test_fitfest_ai_deterministic_queries(client, seed_test_data):
    """Test AI assistant with all FIT-FEST test phrases."""
    _, pat_token = get_tokens(client)
    headers = {"Authorization": f"Bearer {pat_token}"}

    queries = [
        "tell me about citrazine",
        "Who are the available doctors?",
        "How do I book an appointment?",
        "What departments are available?",
        "Which blood group is available?",
        "Where is the blood bank?",
        "Request an ambulance",
        "How can I cancel my appointment?",
        "What are the clinic timings?",
        "Show available ambulance information",
        "Show emergency requests"
    ]

    for q in queries:
        resp = client.post("/api/ai/chat", json={"message": q}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        reply = data.get("reply") or data.get("response")
        assert reply is not None and len(reply) > 10
        assert "Error connecting to hospital AI" not in reply


