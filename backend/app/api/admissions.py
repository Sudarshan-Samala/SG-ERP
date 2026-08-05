from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.admission_service import get_enquiries, create_enquiry
from app.schemas.admission import AdmissionEnquiry, AdmissionEnquiryCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/enquiries", response_model=List[AdmissionEnquiry])
def read_enquiries(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("admissions.read"))):
    return get_enquiries(db, organization_id=current_org.id)

@router.post("/enquiries", response_model=AdmissionEnquiry)
def create_enquiry_endpoint(enquiry_in: AdmissionEnquiryCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("admissions.manage"))):
    return create_enquiry(db, enquiry_in, organization_id=current_org.id)
