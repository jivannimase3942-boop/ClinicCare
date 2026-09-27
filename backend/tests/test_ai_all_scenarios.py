import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_cetirizine():
    res = client.post("/api/ai/chat", json={"message": "Tell me about cetirizine."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Cetirizine" in data["response"]
    assert "Antihistamine" in data["response"] or "antihistamine" in data["response"]
    assert data["intent"] == "medication_info"


def test_ai_doctors_available():
    res = client.post("/api/ai/chat", json={"message": "What doctors are available?"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Specialist" in data["response"] or "Doctor" in data["response"] or "Dr." in data["response"]
    assert data["intent"] == "doctor_discovery"


def test_ai_available_slots():
    res = client.post("/api/ai/chat", json={"message": "Show me available appointment slots."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Slot Availability" in data["response"]
    assert data["intent"] == "check_slots"


def test_ai_book_appointment():
    res = client.post("/api/ai/chat", json={"message": "I want to book an appointment."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["intent"] in ["book_appointment", "doctor_discovery"]


def test_ai_cancel_appointment():
    res = client.post("/api/ai/chat", json={"message": "I want to cancel my appointment."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "cancel" in data["response"].lower()
    assert data["intent"] == "cancel_appointment"


def test_ai_hospital_location():
    res = client.post("/api/ai/chat", json={"message": "Where is the hospital?"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Address" in data["response"]
    assert data["intent"] == "hospital_info"


def test_ai_check_report():
    res = client.post("/api/ai/chat", json={"message": "I need to check my report."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "report" in data["response"].lower()
    assert data["intent"] == "check_report_status"


def test_ai_voice_call():
    res = client.post("/api/ai/chat", json={"message": "I want a voice call."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "voice call" in data["response"].lower()
    assert data["intent"] == "request_voice_call"


def test_ai_front_desk():
    res = client.post("/api/ai/chat", json={"message": "I want to talk to the front desk."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "front desk" in data["response"].lower() or "reception" in data["response"].lower()
    assert data["intent"] == "escalate_to_front_desk"


def test_ai_chest_pain_emergency():
    res = client.post("/api/ai/chat", json={"message": "I have severe chest pain."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_emergency"] is True
    assert data["escalation_triggered"] is True
    assert "EMERGENCY DETECTED" in data["response"]
