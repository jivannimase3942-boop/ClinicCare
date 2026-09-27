from datetime import date, timedelta
import pytest
from app.core.config import settings
from app.models.appointment import Appointment
from app.models.report import Report
from app.models.feedback import Feedback
from app.models.escalation import Escalation
from app.models.error_log import ErrorLog


def test_n8n_workflow_http_endpoints_suite(client, db_session, seed_test_data):
    """Verifies every HTTP endpoint used by the 29 nodes in n8n workflow."""
    pat = seed_test_data["patient"]
    doc = seed_test_data["doctor"]
    workflow_headers = {"Authorization": f"Bearer {settings.AUTOMATED_WORKFLOW_KEY}"}

    # 1. Node 11: GET /api/doctors
    res = client.get("/api/doctors")
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1

    # 2. Node 12: GET /api/doctors/{id}/slots
    test_date = (date.today() + timedelta(days=2)).isoformat()
    res = client.get(f"/api/doctors/{doc.id}/slots?slot_date={test_date}")
    assert res.status_code == 200
    slots = res.json()["data"]

    # 3. Node 13: POST /api/appointments
    res = client.post(
        "/api/appointments",
        json={
            "doctor_id": doc.id,
            "patient_id": pat.id,
            "appointment_date": test_date,
            "appointment_time": "11:00",
            "reason": "Cardiology routine review",
        }
    )
    assert res.status_code == 201
    app_id = res.json()["data"]["id"]

    # 4. Node 14: POST /api/appointments/{id}/reschedule
    res = client.post(
        f"/api/appointments/{app_id}/reschedule",
        json={
            "new_date": test_date,
            "new_time": "14:00",
            "reason": "Rescheduled to afternoon slot",
        }
    )
    assert res.status_code == 200
    assert res.json()["data"]["appointment_time"] == "14:00"

    # 5. Node 15: POST /api/appointments/{id}/cancel
    res = client.post(
        f"/api/appointments/{app_id}/cancel",
        json={
            "cancelled_reason": "Travel conflict",
        }
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "cancelled"

    # 6. Node 16: GET /api/reports
    res = client.get("/api/reports", params={"patient_id": pat.id})
    assert res.status_code == 200

    # 7. Node 17: POST /api/voice/request
    res = client.post(
        "/api/voice/request",
        json={
            "patient_id": pat.id,
            "phone": "+15551234567",
            "reason": "Patient inquiries about cardiology prescription details",
        }
    )
    assert res.status_code == 201
    assert res.json()["data"]["status"] == "requested"

    # 8. Node 18: POST /api/escalations
    res = client.post(
        "/api/escalations",
        json={
            "patient_id": pat.id,
            "reason": "billing",
            "priority": "medium",
            "notes": "Insurance claim verification inquiry",
        }
    )
    assert res.status_code == 201
    assert res.json()["data"]["status"] == "open"

    # 9. Node 7: POST /api/feedback
    res = client.post(
        "/api/feedback",
        json={
            "patient_id": pat.id,
            "rating": 5,
            "comment": "Doctor was attentive and very professional.",
        }
    )
    assert res.status_code == 201
    assert res.json()["data"]["rating"] == 5

    # 10. Node 21: POST /api/admin/tasks/scan-reminders
    res = client.post("/api/admin/tasks/scan-reminders", headers=workflow_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 11. Node 23: POST /api/admin/tasks/scan-feedback
    res = client.post("/api/admin/tasks/scan-feedback", headers=workflow_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 12. Node 25: POST /api/admin/tasks/scan-reports
    res = client.post("/api/admin/tasks/scan-reports", headers=workflow_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 13. Node 29: POST /api/admin/errors
    res = client.post(
        "/api/admin/errors",
        json={
            "service_name": "n8n-engine",
            "error_level": "CRITICAL",
            "message": "Outbound WhatsApp webhook rate limit alert",
            "endpoint": "Patient WhatsApp AI Agent",
        },
        headers=workflow_headers,
    )
    assert res.status_code == 201
    assert res.json()["data"]["error_level"] == "CRITICAL"

    # 14. Node 24: POST /report-ready-webhook
    res = client.post("/report-ready-webhook", json={"event": "report_generated"})
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"


@pytest.mark.parametrize(
    "token",
    [
        "AUTOMATED_WORKFLOW_KEY",
        "cliniccare-workflow-secret-key-2026",
        "carepulse-workflow-secret-key-2026",
    ],
)
def test_legacy_workflow_tokens_are_rejected(client, token):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
