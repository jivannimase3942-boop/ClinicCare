from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.facility import FacilityResponse, FacilityCreate
from app.services.facility_service import facility_service
from app.api.dependencies import require_roles

router = APIRouter(prefix="/facilities", tags=["Healthcare Facilities"])


@router.get("", response_model=ApiResponse[List[FacilityResponse]])
def list_facilities(
    city: Optional[str] = Query(None),
    facility_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    facilities = facility_service.get_all_facilities(db, city=city, facility_type=facility_type, search=search)
    return ApiResponse(success=True, data=facilities)


@router.post("", response_model=ApiResponse[FacilityResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "FRONT_DESK"]))])
def create_facility(data: FacilityCreate, db: Session = Depends(get_db)):
    try:
        fac = facility_service.create_facility(db, data)
        return ApiResponse(success=True, message="Facility created successfully", data=fac)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
