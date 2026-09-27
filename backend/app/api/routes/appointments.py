from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentCancel, AppointmentResponse
from app.services.appointment_service import appointment_service
from app.api.dependencies import get_current_patient, get_optional_patient
from app.models.user import Patient, User

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=ApiResponse[AppointmentResponse], status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_patient:
            target_patient_id = current_patient.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.patient_phone:
            user = db.query(User).filter(User.phone == data.patient_phone).first()
            if not user:
                user = User(
                    email=f"patient_{data.patient_phone.replace('+', '')}@citycarehospital.com",
                    full_name=data.patient_name or "WhatsApp Patient",
                    phone=data.patient_phone,
                    role="PATIENT",
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            if not user.patient_profile:
                pat = Patient(user_id=user.id)
                db.add(pat)
                db.commit()
                db.refresh(pat)
                target_patient_id = pat.id
            else:
                target_patient_id = user.patient_profile.id
        else:
            first_patient = db.query(Patient).first()
            if first_patient:
                target_patient_id = first_patient.id
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient profile found")

        app = appointment_service.book_appointment(
            db=db,
            patient_id=target_patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            appointment_time=data.appointment_time,
            reason=data.reason,
            notes=data.notes,
        )
        return ApiResponse(success=True, message="Appointment booked successfully", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Booking error: {str(e)}")


@router.get("", response_model=ApiResponse[List[AppointmentResponse]])
@router.get("/my", response_model=ApiResponse[List[AppointmentResponse]])
def get_my_appointments(
    patient_id: Optional[str] = Query(None, description="Optional patient ID filter"),
    phone: Optional[str] = Query(None, description="Optional patient phone filter"),
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    target_patient_id = None
    if current_patient:
        target_patient_id = current_patient.id
    elif patient_id:
        target_patient_id = patient_id
    elif phone:
        user = db.query(User).filter(User.phone == phone).first()
        if user and user.patient_profile:
            target_patient_id = user.patient_profile.id
    else:
        first_patient = db.query(Patient).first()
        if first_patient:
            target_patient_id = first_patient.id

    if not target_patient_id:
        return ApiResponse(success=True, data=[])

    apps = appointment_service.get_patient_appointments(db, target_patient_id)
    return ApiResponse(success=True, data=apps)


@router.get("/{id}", response_model=ApiResponse[AppointmentResponse])
def get_appointment(
    id: str,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    patient_id = current_patient.id if current_patient else None
    app = appointment_service.get_appointment_by_id(db, appointment_id=id, patient_id=patient_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found or unauthorized")
    return ApiResponse(success=True, data=app)


def _handle_reschedule(
    id: str,
    data: AppointmentReschedule,
    current_patient: Optional[Patient],
    db: Session,
):
    try:
        patient_id = current_patient.id if current_patient else None
        app = appointment_service.reschedule_appointment(
            db=db,
            appointment_id=id,
            new_date=data.new_date,
            new_time=data.new_time,
            patient_id=patient_id,
            reason=data.reason,
        )
        return ApiResponse(success=True, message="Appointment rescheduled successfully", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{id}/reschedule", response_model=ApiResponse[AppointmentResponse])
def reschedule_appointment_patch(
    id: str,
    data: AppointmentReschedule,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    return _handle_reschedule(id, data, current_patient, db)


@router.post("/{id}/reschedule", response_model=ApiResponse[AppointmentResponse])
def reschedule_appointment_post(
    id: str,
    data: AppointmentReschedule,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    return _handle_reschedule(id, data, current_patient, db)


def _handle_cancel(
    id: str,
    data: AppointmentCancel,
    current_patient: Optional[Patient],
    db: Session,
):
    try:
        patient_id = current_patient.id if current_patient else None
        app = appointment_service.cancel_appointment(
            db=db,
            appointment_id=id,
            patient_id=patient_id,
            cancelled_reason=data.get_reason(),
        )
        return ApiResponse(success=True, message="Appointment cancelled successfully", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{id}/cancel", response_model=ApiResponse[AppointmentResponse])
def cancel_appointment_patch(
    id: str,
    data: AppointmentCancel,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    return _handle_cancel(id, data, current_patient, db)


@router.post("/{id}/cancel", response_model=ApiResponse[AppointmentResponse])
def cancel_appointment_post(
    id: str,
    data: AppointmentCancel,
    current_patient: Optional[Patient] = Depends(get_optional_patient),
    db: Session = Depends(get_db)
):
    return _handle_cancel(id, data, current_patient, db)
