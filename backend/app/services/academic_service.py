from sqlalchemy.orm import Session
from app.models.base import AcademicYear
from app.schemas.academic_year import AcademicYearCreate
from uuid import UUID

def get_academic_years(db: Session, organization_id: UUID):
    return db.query(AcademicYear).filter(AcademicYear.organization_id == organization_id).all()

def create_academic_year(db: Session, ay_in: AcademicYearCreate, organization_id: UUID):
    ay = AcademicYear(
        name=ay_in.name,
        start_date=ay_in.start_date,
        end_date=ay_in.end_date,
        is_active=ay_in.is_active,
        organization_id=organization_id,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay
