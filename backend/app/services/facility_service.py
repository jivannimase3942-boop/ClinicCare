from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.facility import Facility
from app.schemas.facility import FacilityResponse, FacilityCreate


class FacilityService:
    @staticmethod
    def get_all_facilities(
        db: Session,
        city: Optional[str] = None,
        facility_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[FacilityResponse]:
        query = db.query(Facility).filter(Facility.is_active == True)
        if city:
            query = query.filter(Facility.city.ilike(f"%{city}%"))
        if facility_type:
            query = query.filter(Facility.facility_type.ilike(f"%{facility_type}%"))
        if search:
            s = f"%{search}%"
            query = query.filter(Facility.name.ilike(s) | Facility.services.ilike(s) | Facility.address.ilike(s))

        facilities = query.order_by(Facility.name.asc()).all()
        return [FacilityResponse.model_validate(f) for f in facilities]

    @staticmethod
    def create_facility(db: Session, data: FacilityCreate) -> FacilityResponse:
        fac = Facility(
            name=data.name,
            facility_type=data.facility_type or "Multispeciality Hospital",
            services=data.services,
            address=data.address,
            city=data.city,
            phone=data.phone,
            emergency_hotline=data.emergency_hotline,
            operating_hours=data.operating_hours or "24/7 Emergency & Inpatient",
            is_emergency_ready=data.is_emergency_ready if data.is_emergency_ready is not None else True,
            rating=data.rating or 4.8,
            is_active=True,
        )
        db.add(fac)
        db.commit()
        db.refresh(fac)
        return FacilityResponse.model_validate(fac)


facility_service = FacilityService()
