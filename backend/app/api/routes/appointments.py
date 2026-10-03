from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentCancel,
    AppointmentResponse,
    WalkInCreate,
    AppointmentQueueUpdate,
    WaitlistCreate,
    WaitlistResponse,
)
from app.services.appointment_service import appointment_service
from app.api.dependencies import get_current_user, get_optional_user, require_roles
from app.models.user import Patient, User, Doctor

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=ApiResponse[AppointmentResponse], status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    try:
        target_patient_id = None
        if current_user and current_user.role == "PATIENT":
            # Strict patient privacy: Patient cannot book on behalf of another patient
            if not current_user.patient_profile:
                pat = Patient(user_id=current_user.id)
                db.add(pat)
                db.commit()
                db.refresh(pat)
                target_patient_id = pat.id
            else:
                target_patient_id = current_user.patient_profile.id
        elif data.patient_id:
            target_patient_id = data.patient_id
        elif data.patient_phone:
            u = db.query(User).filter(User.phone == data.patient_phone).first()
            if u and u.patient_profile:
                target_patient_id = u.patient_profile.id
            else:
                new_u = User(
                    email=f"patient_{data.patient_phone.replace('+', '')}@citycarehospital.com",
                    full_name=data.patient_name or "Hospital Patient",
                    phone=data.patient_phone,
                    role="PATIENT",
                    is_active=True,
                    password_hash="system_registered"
                )
                db.add(new_u)
                db.commit()
                db.refresh(new_u)
                pat = Patient(user_id=new_u.id)
                db.add(pat)
                db.commit()
                db.refresh(pat)
                target_patient_id = pat.id
        elif current_user and current_user.patient_profile:
            target_patient_id = current_user.patient_profile.id
        else:
            first_patient = db.query(Patient).first()
            if first_patient:
                target_patient_id = first_patient.id
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient profile found for booking")

        user_clinic = current_user.clinic_id if current_user else None
        app = appointment_service.book_appointment(
            db=db,
            patient_id=target_patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            appointment_time=data.appointment_time,
            reason=data.reason,
            notes=data.notes,
            clinic_id=user_clinic,
            appointment_type=data.appointment_type or "NEW_CONSULTATION",
            is_walk_in=bool(data.is_walk_in),
            parent_appointment_id=data.parent_appointment_id,
        )
        return ApiResponse(success=True, message="Appointment booked successfully", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Booking error: {str(e)}")


@router.post("/walk-in", response_model=ApiResponse[AppointmentResponse], status_code=status.HTTP_201_CREATED)
def create_walk_in(
    data: WalkInCreate,
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "SUPER_ADMIN", "DOCTOR"])),
    db: Session = Depends(get_db)
):
    try:
        # Find or create patient
        u = db.query(User).filter(User.phone == data.patient_phone).first()
        if not u:
            # Generate email if not given
            email = data.patient_email or f"walkin_{data.patient_phone.replace('+', '')}@citycarehospital.com"
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                email = f"walkin_{data.patient_phone.replace('+', '')}_{int(date.today().strftime('%s', 0) if hasattr(date.today(), 'timestamp') else '101')}@citycarehospital.com"
            u = User(
                email=email,
                full_name=data.patient_name,
                phone=data.patient_phone,
                role="PATIENT",
                clinic_id=current_user.clinic_id,
                is_active=True,
                password_hash="system_walkin"
            )
            db.add(u)
            db.commit()
            db.refresh(u)

        if not u.patient_profile:
            pat = Patient(user_id=u.id)
            db.add(pat)
            db.commit()
            db.refresh(pat)
            patient_id = pat.id
        else:
            patient_id = u.patient_profile.id

        # Determine current time
        from datetime import datetime, timezone
        now_time = datetime.now(timezone.utc).strftime("%H:%M")

        app = appointment_service.book_appointment(
            db=db,
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            appointment_date=date.today(),
            appointment_time=now_time,
            reason=data.reason or "Walk-in consultation",
            clinic_id=current_user.clinic_id,
            appointment_type=data.appointment_type or "NEW_CONSULTATION",
            is_walk_in=True,
        )
        return ApiResponse(success=True, message=f"Walk-in registered. Token: {app.token_number}", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Walk-in error: {str(e)}")


@router.post("/{id}/check-in", response_model=ApiResponse[AppointmentResponse])
def check_in(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = appointment_service.get_appointment_by_id(db, appointment_id=id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Patient privacy
    if current_user.role == "PATIENT":
        if not current_user.patient_profile or app.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif current_user.role in ["ADMIN", "FRONT_DESK"]:
        if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and app.clinic_id and current_user.clinic_id != app.clinic_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Different clinic")

    try:
        updated = appointment_service.check_in_appointment(db, appointment_id=id, actor_id=current_user.id)
        return ApiResponse(success=True, message=f"Checked in successfully. Token: {updated.token_number}", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{id}/queue", response_model=ApiResponse[AppointmentResponse])
def update_queue(
    id: str,
    data: AppointmentQueueUpdate,
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    app = appointment_service.get_appointment_by_id(db, appointment_id=id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and app.clinic_id and current_user.clinic_id != app.clinic_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Different clinic")

    try:
        updated = appointment_service.update_queue_status(
            db=db,
            appointment_id=id,
            queue_status=data.queue_status,
            notes=data.notes,
            actor_id=current_user.id
        )
        return ApiResponse(success=True, message="Queue status updated", data=updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/queue/today", response_model=ApiResponse[List[AppointmentResponse]])
def get_today_queue(
    doctor_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    doc_filter = doctor_id
    if current_user.role == "DOCTOR" and current_user.doctor_profile:
        doc_filter = current_user.doctor_profile.id

    queue_list = appointment_service.get_today_queue(db, clinic_id=clinic_filter, doctor_id=doc_filter)
    return ApiResponse(success=True, data=queue_list)


@router.post("/waitlist", response_model=ApiResponse[WaitlistResponse], status_code=status.HTTP_201_CREATED)
def join_waitlist(
    data: WaitlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_pid = None
    if current_user.role == "PATIENT":
        if not current_user.patient_profile:
            pat = Patient(user_id=current_user.id)
            db.add(pat)
            db.commit()
            db.refresh(pat)
            target_pid = pat.id
        else:
            target_pid = current_user.patient_profile.id
    else:
        first_pat = db.query(Patient).first()
        target_pid = first_pat.id if first_pat else None

    if not target_pid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patient found to join waitlist")

    try:
        wl = appointment_service.add_to_waitlist(
            db=db,
            patient_id=target_pid,
            doctor_id=data.doctor_id,
            desired_date=data.desired_date,
            preferred_time_range=data.preferred_time_range,
            notes=data.notes,
            clinic_id=current_user.clinic_id,
        )
        resp = WaitlistResponse(
            id=wl.id,
            clinic_id=wl.clinic_id,
            patient_id=wl.patient_id,
            patient_name=wl.patient.user.full_name if wl.patient and wl.patient.user else "Patient",
            patient_phone=wl.patient.user.phone if wl.patient and wl.patient.user else None,
            doctor_id=wl.doctor_id,
            doctor_name=wl.doctor.user.full_name if wl.doctor and wl.doctor.user else "Doctor",
            desired_date=wl.desired_date,
            preferred_time_range=wl.preferred_time_range,
            status=wl.status,
            notes=wl.notes,
            created_at=wl.created_at,
        )
        return ApiResponse(success=True, message="Added to waitlist", data=resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/waitlist", response_model=ApiResponse[List[WaitlistResponse]])
def get_waitlist_items(
    doctor_id: Optional[str] = Query(None),
    desired_date: Optional[date] = Query(None),
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "DOCTOR", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
    items = appointment_service.get_waitlist(db, clinic_id=clinic_filter, doctor_id=doctor_id, desired_date=desired_date)
    result = []
    for wl in items:
        result.append(
            WaitlistResponse(
                id=wl.id,
                clinic_id=wl.clinic_id,
                patient_id=wl.patient_id,
                patient_name=wl.patient.user.full_name if wl.patient and wl.patient.user else "Patient",
                patient_phone=wl.patient.user.phone if wl.patient and wl.patient.user else None,
                doctor_id=wl.doctor_id,
                doctor_name=wl.doctor.user.full_name if wl.doctor and wl.doctor.user else "Doctor",
                desired_date=wl.desired_date,
                preferred_time_range=wl.preferred_time_range,
                status=wl.status,
                notes=wl.notes,
                created_at=wl.created_at,
            )
        )
    return ApiResponse(success=True, data=result)


@router.post("/waitlist/{id}/convert", response_model=ApiResponse[AppointmentResponse])
def convert_waitlist(
    id: str,
    appointment_time: str = Query(..., description="Format HH:MM e.g. 11:30"),
    current_user: User = Depends(require_roles(["ADMIN", "FRONT_DESK", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    try:
        app = appointment_service.convert_waitlist_to_appointment(db, waitlist_id=id, appointment_time=appointment_time)
        return ApiResponse(success=True, message="Waitlist converted to confirmed appointment", data=app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=ApiResponse[List[AppointmentResponse]])
@router.get("/my", response_model=ApiResponse[List[AppointmentResponse]])
def get_my_appointments(
    patient_id: Optional[str] = Query(None, description="Optional patient ID filter for admin"),
    phone: Optional[str] = Query(None, description="Optional patient phone filter for admin"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "PATIENT":
        # Privacy: patient strictly sees only their own appointments
        if not current_user.patient_profile:
            return ApiResponse(success=True, data=[])
        apps = appointment_service.get_patient_appointments(db, current_user.patient_profile.id)
        return ApiResponse(success=True, data=apps)

    if current_user.role == "DOCTOR":
        doc_id = current_user.doctor_profile.id if current_user.doctor_profile else None
        apps = appointment_service.get_all_appointments(db, doctor_id=doc_id)
        return ApiResponse(success=True, data=apps)

    if current_user.role in ["ADMIN", "FRONT_DESK"]:
        target_pid = patient_id
        if not target_pid and phone:
            u = db.query(User).filter(User.phone == phone).first()
            if u and u.patient_profile:
                target_pid = u.patient_profile.id
        if target_pid:
            apps = appointment_service.get_patient_appointments(db, target_pid)
        else:
            clinic_filter = current_user.clinic_id if current_user.role != "SUPER_ADMIN" else None
            apps = appointment_service.get_all_appointments(db, clinic_id=clinic_filter)
        return ApiResponse(success=True, data=apps)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/{id}", response_model=ApiResponse[AppointmentResponse])
def get_appointment(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    app = appointment_service.get_appointment_by_id(db, appointment_id=id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Patient privacy check: Patient can only view their own appointment
    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or app.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another patient's appointment")

    # Doctor privacy check: Doctor can only view their assigned appointments
    if current_user and current_user.role == "DOCTOR":
        if not current_user.doctor_profile or app.doctor_id != current_user.doctor_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot view another doctor's appointment")

    # Clinic tenant isolation check: Staff cannot access appointment belonging to another clinic
    if current_user and current_user.role in ["ADMIN", "FRONT_DESK"]:
        if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and app.clinic_id and current_user.clinic_id != app.clinic_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot access appointment of another clinic")

    return ApiResponse(success=True, data=app)


def _handle_reschedule(
    id: str,
    data: AppointmentReschedule,
    current_user: Optional[User],
    db: Session,
):
    app = appointment_service.get_appointment_by_id(db, appointment_id=id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or app.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot modify another patient's appointment")
    elif current_user and current_user.role in ["ADMIN", "FRONT_DESK"]:
        if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and app.clinic_id and current_user.clinic_id != app.clinic_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot reschedule appointment of another clinic")
    elif current_user and current_user.role not in ["ADMIN", "FRONT_DESK", "DOCTOR"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        updated_app = appointment_service.reschedule_appointment(
            db=db,
            appointment_id=id,
            new_date=data.new_date,
            new_time=data.new_time,
            patient_id=None,
            reason=data.reason,
        )
        return ApiResponse(success=True, message="Appointment rescheduled successfully", data=updated_app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{id}/reschedule", response_model=ApiResponse[AppointmentResponse])
def reschedule_appointment_patch(
    id: str,
    data: AppointmentReschedule,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    return _handle_reschedule(id, data, current_user, db)


@router.post("/{id}/reschedule", response_model=ApiResponse[AppointmentResponse])
def reschedule_appointment_post(
    id: str,
    data: AppointmentReschedule,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    return _handle_reschedule(id, data, current_user, db)


def _handle_cancel(
    id: str,
    data: AppointmentCancel,
    current_user: Optional[User],
    db: Session,
):
    app = appointment_service.get_appointment_by_id(db, appointment_id=id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if current_user and current_user.role == "PATIENT":
        if not current_user.patient_profile or app.patient_id != current_user.patient_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot cancel another patient's appointment")
    elif current_user and current_user.role in ["ADMIN", "FRONT_DESK"]:
        if current_user.role != "SUPER_ADMIN" and current_user.clinic_id and app.clinic_id and current_user.clinic_id != app.clinic_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot cancel appointment of another clinic")
    elif current_user and current_user.role not in ["ADMIN", "FRONT_DESK", "DOCTOR"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        updated_app = appointment_service.cancel_appointment(
            db=db,
            appointment_id=id,
            patient_id=None,
            cancelled_reason=data.get_reason(),
        )
        return ApiResponse(success=True, message="Appointment cancelled successfully", data=updated_app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{id}/cancel", response_model=ApiResponse[AppointmentResponse])
def cancel_appointment_patch(
    id: str,
    data: AppointmentCancel,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    return _handle_cancel(id, data, current_user, db)


@router.post("/{id}/cancel", response_model=ApiResponse[AppointmentResponse])
def cancel_appointment_post(
    id: str,
    data: AppointmentCancel,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    return _handle_cancel(id, data, current_user, db)
