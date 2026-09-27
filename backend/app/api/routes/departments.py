from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.doctor import DepartmentResponse
from app.services.doctor_service import doctor_service

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=ApiResponse[List[DepartmentResponse]])
def list_departments(db: Session = Depends(get_db)):
    depts = doctor_service.get_departments(db)
    return ApiResponse(success=True, data=depts)


@router.get("/{id}", response_model=ApiResponse[DepartmentResponse])
def get_department(id: str, db: Session = Depends(get_db)):
    dept = doctor_service.get_department_by_id(db, id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return ApiResponse(success=True, data=DepartmentResponse.model_validate(dept))
