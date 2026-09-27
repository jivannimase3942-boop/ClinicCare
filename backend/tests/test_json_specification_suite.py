from datetime import date, timedelta
import pytest
from app.core.config import settings
from app.models.appointment import Appointment
from app.models.report import Report
from app.models.feedback import Feedback
from app.models.escalation import Escalation
from app.models.error_log import ErrorLog
from app.ai.tools import (
    get_hospital_doctor_info,
    check_doctor_booked_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    check_my_report_status,
    request_ai_voice_call,
    escalate_to_front_desk,
)
from app.services.appointment_service import appointment_service
from app.services.feedback_service import feedback_service
from app.services.report_service import report_service
from app.services.error_service import error_service
from app.services.voice_service import voice_service


def test_webhook_get_handshake(client):
    """Verifies GET /whatsapp-webhook Meta verification handshake."""
    resp = client.get(
        "/whatsapp-webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WA_VERIFY_TOKEN,
            "hub.challenge": "challenge_code_987654321",
        }
    )
    assert resp.status_code == 200
    assert resp.text == "challenge_code_987654321"

    # Invalid token test
    invalid_resp = client.get(
        "/whatsapp-webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_code_987654321",
        }
    )
    assert invalid_resp.status_code == 403


def test_webhook_post_inbound(client, seed_test_data):
    """Verifies POST /whatsapp-webhook with realistic WhatsApp payload."""
    pat_phone = seed_test_data["patient_user"].phone
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15550001", "phone_number_id": "12345"},
                            "contacts": [{"profile": {"name": "John Patient"}, "wa_id": pat_phone}],
                            "messages": [
                                {
                                    "from": pat_phone,
                                    "id": "wamid.HBgLMTU1",
                                    "timestamp": "1700000000",
                                    "text": {"body": "Hello, what are the hospital consulting hours?"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    resp = client.post("/whatsapp-webhook", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "EVENT_RECEIVED"
    assert data["detail"]["status"] == "processed"


def test_scenario_1_hospital_doctor_info(db_session, seed_test_data):
    """TEST 1: Patient asks hospital/doctor information."""
    info = get_hospital_doctor_info(db_session)
    assert info["hospital_name"] == settings.HOSPITAL_NAME
    assert len(info["departments"]) >= 1
    assert len(info["doctors"]) >= 1
    assert info["doctors"][0]["department"] == "Cardiology"
    assert info["doctors"][0]["fee"] == 100.0


def test_scenario_2_doctor_available_slots(db_session, seed_test_data):
    """TEST 2: Patient asks for available appointment slots."""
    doc_id = seed_test_data["doctor"].id
    target_date = date.today() + timedelta(days=2)
    slots = check_doctor_booked_slots(db_session, doc_id, target_date)
    assert slots["doctor_id"] == doc_id
    assert slots["total_slots"] > 0
    assert len(slots["available_slots"]) > 0


def test_scenario_3_book_appointment(db_session, seed_test_data):
    """TEST 3: Patient books an appointment."""
    pat_id = seed_test_data["patient"].id
    doc_id = seed_test_data["doctor"].id
    book_date = date.today() + timedelta(days=3)
    res = book_appointment(db_session, pat_id, doc_id, book_date, "10:00", "Regular checkup")
    assert res["success"] is True
    assert res["status"] == "confirmed"

    # Verify database persistence
    saved_app = db_session.query(Appointment).filter(Appointment.id == res["appointment_id"]).first()
    assert saved_app is not None
    assert saved_app.doctor_id == doc_id
    assert saved_app.appointment_date == book_date


def test_scenario_4_and_5_check_and_cancel_appointment(db_session, seed_test_data):
    """TEST 4 & 5: Patient queries existing appointment and cancels it."""
    pat_id = seed_test_data["patient"].id
    doc_id = seed_test_data["doctor"].id
    book_date = date.today() + timedelta(days=4)
    res = book_appointment(db_session, pat_id, doc_id, book_date, "11:00", "Test Appointment")
    app_id = res["appointment_id"]

    # TEST 4: Query existing appointment
    app = appointment_service.get_appointment_by_id(db_session, app_id, pat_id)
    assert app is not None
    assert app.status == "confirmed"

    # TEST 5: Cancel appointment
    cancel_res = cancel_appointment(db_session, pat_id, app_id, "Schedule conflict")
    assert cancel_res["success"] is True
    assert cancel_res["status"] == "cancelled"

    # Verify in DB
    refreshed = db_session.query(Appointment).filter(Appointment.id == app_id).first()
    assert refreshed.status == "cancelled"


def test_scenario_6_reschedule_appointment(db_session, seed_test_data):
    """TEST 6: Patient reschedules appointment."""
    pat_id = seed_test_data["patient"].id
    doc_id = seed_test_data["doctor"].id
    orig_date = date.today() + timedelta(days=5)
    new_date = date.today() + timedelta(days=6)
    
    booked = book_appointment(db_session, pat_id, doc_id, orig_date, "14:00", "Initial consultation")
    app_id = booked["appointment_id"]

    resched = reschedule_appointment(db_session, pat_id, app_id, new_date, "15:00", "Updated availability")
    assert resched["success"] is True
    assert resched["new_date"] == new_date.isoformat()
    assert resched["new_time"] == "15:00"


def test_scenario_7_request_ai_voice_call(db_session, seed_test_data):
    """TEST 7: Patient requests AI voice call."""
    pat_id = seed_test_data["patient"].id
    res = request_ai_voice_call(db_session, pat_id, "+1555123456", "Need guidance on preoperative instructions")
    assert res["success"] is True
    assert res["status"] == "requested"
    assert "request_id" in res


def test_scenario_8_and_9_reports_ready_and_status(db_session, seed_test_data):
    """TEST 8 & 9: Diagnostic report becomes ready & patient checks status."""
    pat_id = seed_test_data["patient"].id
    doc_id = seed_test_data["doctor"].id

    rep = Report(
        patient_id=pat_id,
        doctor_id=doc_id,
        title="Complete Blood Count",
        report_type="Pathology",
        status="ready",
        file_url="https://cliniccare.hospital/reports/secure/cbc_report.pdf",
        report_date=date.today(),
    )
    db_session.add(rep)
    db_session.commit()

    # TEST 8: Trigger report scanner
    scan_res = report_service.scan_and_send_report_notifications(db_session)
    assert scan_res["scanned"] >= 1
    assert scan_res["notifications_sent"] >= 1

    # TEST 9: Patient retrieves reports
    status_flow = check_my_report_status(db_session, pat_id)
    assert status_flow["count"] >= 1
    assert status_flow["reports"][0]["status"] == "ready"


def test_scenario_10_and_11_feedback_workflow_and_rating(client, db_session, seed_test_data):
    """TEST 10 & 11: Completed appointment enters feedback workflow & patient sends rating 1-5."""
    pat_id = seed_test_data["patient"].id
    doc_id = seed_test_data["doctor"].id
    pat_phone = seed_test_data["patient_user"].phone

    # Create completed appointment
    completed_app = Appointment(
        patient_id=pat_id,
        doctor_id=doc_id,
        appointment_date=date.today() - timedelta(days=1),
        appointment_time="09:30",
        status="completed",
        reason="Follow up consultation",
    )
    db_session.add(completed_app)
    db_session.commit()
    db_session.refresh(completed_app)

    # TEST 10: Feedback scanner detects unrated completed appointment
    fb_scan = feedback_service.scan_and_send_feedback_requests(db_session)
    assert fb_scan["scanned"] >= 1
    assert fb_scan["feedback_requests_sent"] >= 1

    # TEST 11: Patient sends rating 1-5 via WhatsApp webhook
    rating_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": pat_phone,
                                    "id": "wamid.FB_RATING",
                                    "timestamp": "1700000010",
                                    "text": {"body": "5 - Outstanding care by the doctor!"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    resp = client.post("/whatsapp-webhook", json=rating_payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["detail"]["status"] == "feedback_recorded"
    assert res_data["detail"]["rating"] == 5

    # Verify Feedback in DB
    stored_fb = db_session.query(Feedback).filter(Feedback.appointment_id == completed_app.id).first()
    assert stored_fb is not None
    assert stored_fb.rating == 5


def test_scenario_12_complaint_and_escalation(db_session, seed_test_data):
    """TEST 12: Patient raises complaint / emergency -> Escalate to front desk."""
    pat_id = seed_test_data["patient"].id
    esc_res = escalate_to_front_desk(
        db=db_session,
        patient_id=pat_id,
        reason="billing_dispute",
        priority="high",
        notes="Patient inquiries about unexpected lab invoice charge",
    )
    assert esc_res["success"] is True
    assert esc_res["priority"] == "high"

    # Verify Escalation in DB
    esc = db_session.query(Escalation).filter(Escalation.id == esc_res["escalation_id"]).first()
    assert esc is not None
    assert esc.reason == "billing_dispute"
    assert esc.status == "open"


def test_scenario_13_critical_error_workflow(db_session):
    """TEST 13: Critical / error workflow occurs -> builds alert message & logs to error_logs."""
    alert_info = error_service.build_alert_message(
        service_name="appointment-scheduler",
        error_level="CRITICAL",
        message="Database connection pool timeout during slot lock",
        stack_trace="Traceback: File service.py line 42 in lock_slot",
        endpoint="/api/appointments/lock",
        context={"slot_id": "slot-99", "patient_id": "pat-123"}
    )
    assert "CRITICAL" in alert_info["subject"]
    assert "Database connection pool timeout" in alert_info["body"]

    # Log to DB and test alert email dispatch handler
    log_entry = error_service.log_error(
        db=db_session,
        message="Database connection pool timeout during slot lock",
        service_name="appointment-scheduler",
        error_level="CRITICAL",
        stack_trace="Traceback: File service.py line 42 in lock_slot",
        endpoint="/api/appointments/lock",
        context={"slot_id": "slot-99"}
    )
    assert log_entry is not None
    assert log_entry.error_level == "CRITICAL"

