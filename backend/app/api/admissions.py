from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.services.admission_service import get_enquiries, create_enquiry
from app.schemas.admission import AdmissionEnquiry, AdmissionEnquiryCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/enquiries", response_model=List[AdmissionEnquiry])
def read_enquiries(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("admissions.read"))):
    branch_ids = None if current_user.is_superuser else accessible_branch_ids(current_user)
    return get_enquiries(db, organization_id=current_org.id, branch_ids=branch_ids)

@router.post("/enquiries", response_model=AdmissionEnquiry)
def create_enquiry_endpoint(enquiry_in: AdmissionEnquiryCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("admissions.manage"))):
    enforce_branch_access(current_user, enquiry_in.branch_id)
    return create_enquiry(db, enquiry_in, organization_id=current_org.id)
