from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import AcademicYear, AdmissionEnquiry, Branch
from app.schemas.admission import AdmissionEnquiryCreate


def get_enquiries(db: Session, organization_id: UUID, branch_ids: set[UUID] | None = None):
    query = db.query(AdmissionEnquiry).filter(AdmissionEnquiry.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        query = query.filter(AdmissionEnquiry.branch_id.in_(branch_ids))
    return query.order_by(AdmissionEnquiry.created_at.desc()).all()


def create_enquiry(db: Session, enquiry_in: AdmissionEnquiryCreate, organization_id: UUID):
    branch = db.query(Branch).filter(Branch.id == enquiry_in.branch_id, Branch.organization_id == organization_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch does not belong to this organization")
    academic_year = db.query(AcademicYear).filter(AcademicYear.id == enquiry_in.academic_year_id, AcademicYear.organization_id == organization_id).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Academic year does not belong to this organization")

    normalized_email = str(enquiry_in.email).strip().lower()
    normalized_phone = enquiry_in.phone.strip()
    duplicate = db.query(AdmissionEnquiry).filter(
        AdmissionEnquiry.organization_id == organization_id,
        AdmissionEnquiry.branch_id == enquiry_in.branch_id,
        AdmissionEnquiry.academic_year_id == enquiry_in.academic_year_id,
        AdmissionEnquiry.email == normalized_email,
        AdmissionEnquiry.phone == normalized_phone,
        AdmissionEnquiry.status.in_(["ENQUIRY", "APPLIED", "SELECTED"]),
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active enquiry already exists for this contact, branch and academic year")

    payload = enquiry_in.model_dump()
    payload["email"] = normalized_email
    payload["phone"] = normalized_phone
    enquiry = AdmissionEnquiry(**payload, organization_id=organization_id)
    db.add(enquiry); db.commit(); db.refresh(enquiry)
    return enquiry
