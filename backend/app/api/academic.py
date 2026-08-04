from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.academic_service import get_academic_years, create_academic_year
from app.schemas.academic_year import AcademicYear, AcademicYearCreate
from app.models.base import Organization

router = APIRouter()

@router.get("/", response_model=List[AcademicYear])
def read_academic_years(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization)
):
    return get_academic_years(db, organization_id=current_org.id)

@router.post("/", response_model=AcademicYear)
def create_academic_year_endpoint(
    ay_in: AcademicYearCreate,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization)
):
    return create_academic_year(db, ay_in, organization_id=current_org.id)
