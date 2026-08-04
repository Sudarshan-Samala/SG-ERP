from sqlalchemy.orm import Session
from app.models.base import AdmissionEnquiry
from app.schemas.admission import AdmissionEnquiryCreate
from uuid import UUID

def get_enquiries(db: Session, organization_id: UUID):
    return db.query(AdmissionEnquiry).filter(AdmissionEnquiry.organization_id == organization_id).all()

def create_enquiry(db: Session, enquiry_in: AdmissionEnquiryCreate, organization_id: UUID):
    enquiry = AdmissionEnquiry(
        **enquiry_in.dict(),
        organization_id=organization_id,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    return enquiry
