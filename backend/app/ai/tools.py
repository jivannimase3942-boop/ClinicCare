from datetime import date, datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.doctor_service import doctor_service
from app.services.appointment_service import appointment_service
from app.services.report_service import report_service
from app.services.voice_service import voice_service
from app.services.escalation_service import escalation_service
from app.schemas.voice import VoiceCallCreate
from app.core.config import settings


def get_hospital_doctor_info(
    db: Session,
    department_name: Optional[str] = None,
    doctor_name: Optional[str] = None
) -> Dict[str, Any]:
    departments = doctor_service.get_departments(db)
    doctors = doctor_service.get_doctors(db, search=doctor_name or department_name)
    
    return {
        "hospital_name": settings.HOSPITAL_NAME,
        "hospital_phone": settings.HOSPITAL_PHONE,
        "hospital_email": settings.HOSPITAL_EMAIL,
        "hospital_address": settings.HOSPITAL_ADDRESS,
        "emergency_hotline": settings.EMERGENCY_HOTLINE,
        "departments": [{"id": d.id, "name": d.name, "description": d.description} for d in departments],
        "doctors": [
            {
                "id": doc.id,
                "name": doc.full_name,
                "department": doc.department_name,
                "specialization": doc.specialization,
                "qualification": doc.qualification,
                "experience_years": doc.experience_years,
                "fee": doc.consultation_fee,
                "available_days": doc.available_days,
                "available_hours": f"{doc.available_hours_start} - {doc.available_hours_end}",
                "location": doc.location,
            }
            for doc in doctors
        ]
    }


def check_doctor_booked_slots(
    db: Session,
    doctor_id: str,
    slot_date: date
) -> Dict[str, Any]:
    slots = doctor_service.get_or_generate_slots_for_date(db, doctor_id, slot_date)
    available_slots = [s.start_time for s in slots if not s.is_booked]
    booked_slots = [s.start_time for s in slots if s.is_booked]
    
    return {
        "doctor_id": doctor_id,
        "date": slot_date.isoformat(),
        "total_slots": len(slots),
        "available_slots": available_slots,
        "booked_slots": booked_slots,
    }


def book_appointment(
    db: Session,
    patient_id: str,
    doctor_id: str,
    appointment_date: date,
    appointment_time: str,
    reason: Optional[str] = "AI Assistant booking"
) -> Dict[str, Any]:
    try:
        app = appointment_service.book_appointment(
            db=db,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
        )
        return {
            "success": True,
            "appointment_id": app.id,
            "doctor_name": app.doctor_name,
            "department": app.department_name,
            "date": app.appointment_date.isoformat(),
            "time": app.appointment_time,
            "status": app.status,
            "message": f"Appointment booked successfully with Dr. {app.doctor_name} on {app.appointment_date} at {app.appointment_time}."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def reschedule_appointment(
    db: Session,
    patient_id: str,
    appointment_id: str,
    new_date: date,
    new_time: str,
    reason: Optional[str] = "Rescheduled via AI Assistant"
) -> Dict[str, Any]:
    try:
        app = appointment_service.reschedule_appointment(
            db=db,
            appointment_id=appointment_id,
            new_date=new_date,
            new_time=new_time,
            patient_id=patient_id,
            reason=reason,
        )
        return {
            "success": True,
            "appointment_id": app.id,
            "doctor_name": app.doctor_name,
            "new_date": app.appointment_date.isoformat(),
            "new_time": app.appointment_time,
            "status": app.status,
            "message": f"Appointment rescheduled successfully to {app.appointment_date} at {app.appointment_time}."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def cancel_appointment(
    db: Session,
    patient_id: str,
    appointment_id: str,
    reason: Optional[str] = "Cancelled via AI Assistant"
) -> Dict[str, Any]:
    try:
        app = appointment_service.cancel_appointment(
            db=db,
            appointment_id=appointment_id,
            patient_id=patient_id,
            cancelled_reason=reason,
        )
        return {
            "success": True,
            "appointment_id": app.id,
            "status": app.status,
            "message": "Appointment cancelled successfully."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_my_report_status(db: Session, patient_id: str) -> Dict[str, Any]:
    reports = report_service.get_patient_reports(db, patient_id)
    return {
        "count": len(reports),
        "reports": [
            {
                "id": r.id,
                "title": r.title,
                "type": r.report_type,
                "status": r.status,
                "date": r.report_date.isoformat(),
                "doctor": r.doctor_name,
                "file_available": bool(r.file_url)
            }
            for r in reports
        ]
    }


def request_ai_voice_call(
    db: Session,
    patient_id: str,
    phone: str,
    reason: str
) -> Dict[str, Any]:
    try:
        req = voice_service.request_voice_call(
            db=db,
            patient_id=patient_id,
            data=VoiceCallCreate(phone=phone, reason=reason)
        )
        return {
            "success": True,
            "request_id": req.id,
            "status": req.status,
            "message": f"Voice call request placed for {phone}. Our automated assistant will call you shortly."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def escalate_to_front_desk(
    db: Session,
    patient_id: str,
    reason: str,
    priority: str = "medium",
    notes: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    try:
        esc = escalation_service.create_escalation(
            db=db,
            patient_id=patient_id,
            reason=reason,
            priority=priority,
            conversation_id=conversation_id,
            notes=notes,
        )
        return {
            "success": True,
            "escalation_id": esc.id,
            "status": esc.status,
            "priority": esc.priority,
            "message": "Your request has been escalated to our front desk team. A staff member will attend to your request promptly."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_blood_units(db: Session, blood_group: Optional[str] = None, city: Optional[str] = None) -> Dict[str, Any]:
    from app.services.blood_service import blood_service
    results = blood_service.search_blood_group(db, blood_group=blood_group or "", city=city)
    return {
        "count": len(results),
        "results": [
            {
                "blood_bank": r.blood_bank_name,
                "city": r.city,
                "phone": r.phone,
                "blood_group": r.blood_group,
                "units_available": r.units_available,
                "status": r.status,
            }
            for r in results
        ]
    }


def get_available_ambulances_info(db: Session) -> Dict[str, Any]:
    from app.services.ambulance_service import ambulance_service
    ambs = ambulance_service.get_all_ambulances(db)
    return {
        "total_fleet": len(ambs),
        "available_count": sum(1 for a in ambs if a.status == "available"),
        "ambulances": [
            {
                "vehicle_number": a.vehicle_number,
                "type": a.ambulance_type,
                "status": a.status,
                "base_station": a.base_station,
                "driver_phone": a.driver_phone,
            }
            for a in ambs
        ]
    }


def get_clinic_facilities_info(db: Session) -> Dict[str, Any]:
    from app.services.facility_service import facility_service
    facs = facility_service.get_all_facilities(db)
    return {
        "facilities": [
            {
                "name": f.name,
                "type": f.facility_type,
                "city": f.city,
                "services": f.services,
                "hotline": f.emergency_hotline,
                "hours": f.operating_hours,
            }
            for f in facs
        ]
    }


