from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import AcademicYear, AdmissionEnquiry, Branch
from app.schemas.admission import AdmissionEnquiryCreate


def get_enquiries(db: Session, organization_id: UUID):
    return db.query(AdmissionEnquiry).filter(AdmissionEnquiry.organization_id == organization_id).all()


def create_enquiry(db: Session, enquiry_in: AdmissionEnquiryCreate, organization_id: UUID):
    branch = db.query(Branch).filter(Branch.id == enquiry_in.branch_id, Branch.organization_id == organization_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch does not belong to this organization")

    academic_year = db.query(AcademicYear).filter(
        AcademicYear.id == enquiry_in.academic_year_id,
        AcademicYear.organization_id == organization_id,
    ).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Academic year does not belong to this organization")

    enquiry = AdmissionEnquiry(**enquiry_in.model_dump(), organization_id=organization_id)
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    return enquiry
