from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentCancel, AppointmentResponse
from app.services.appointment_service import appointment_service
from app.api.dependencies import get_current_user, get_optional_user, require_roles
from app.models.user import Patient, User

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
            apps = appointment_service.get_all_appointments(db)
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
