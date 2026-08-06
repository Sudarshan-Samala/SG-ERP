from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import AcademicYear, AdmissionEnquiry, Branch
from app.schemas.admission import AdmissionEnquiryCreate
from app.services.audit.audit_service import log_action

ADMISSION_TRANSITIONS = {
    "ENQUIRY": {"APPLIED", "CLOSED"},
    "APPLIED": {"SELECTED", "REJECTED", "CLOSED"},
    "SELECTED": {"ADMITTED", "REJECTED", "CLOSED"},
    "REJECTED": {"APPLIED", "CLOSED"},
    "ADMITTED": set(),
    "CLOSED": set(),
}


def get_enquiries(db: Session, organization_id: UUID, branch_ids: set[UUID] | None = None):
    query = db.query(AdmissionEnquiry).filter(AdmissionEnquiry.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        query = query.filter(AdmissionEnquiry.branch_id.in_(branch_ids))
    return query.order_by(AdmissionEnquiry.created_at.desc()).all()


def create_enquiry(db: Session, enquiry_in: AdmissionEnquiryCreate, organization_id: UUID, user_id: UUID):
    branch = db.query(Branch).filter(Branch.id == enquiry_in.branch_id, Branch.organization_id == organization_id, Branch.is_active.is_(True)).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active branch does not belong to this organization")
    academic_year = db.query(AcademicYear).filter(AcademicYear.id == enquiry_in.academic_year_id, AcademicYear.organization_id == organization_id, AcademicYear.is_active.is_(True)).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active academic year does not belong to this organization")
    normalized_email = str(enquiry_in.email).strip().lower(); normalized_phone = enquiry_in.phone.strip()
    duplicate = db.query(AdmissionEnquiry).filter(AdmissionEnquiry.organization_id == organization_id, AdmissionEnquiry.branch_id == enquiry_in.branch_id, AdmissionEnquiry.academic_year_id == enquiry_in.academic_year_id, AdmissionEnquiry.email == normalized_email, AdmissionEnquiry.phone == normalized_phone, AdmissionEnquiry.status.in_(["ENQUIRY", "APPLIED", "SELECTED"])).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active enquiry already exists for this contact, branch and academic year")
    payload = enquiry_in.model_dump(); payload["email"] = normalized_email; payload["phone"] = normalized_phone
    enquiry = AdmissionEnquiry(**payload, organization_id=organization_id); db.add(enquiry)
    try:
        db.flush(); log_action(db, organization_id, user_id, "CREATE", "ADMISSION_ENQUIRY", enquiry.id, new_values=str(payload)); db.commit(); db.refresh(enquiry); return enquiry
    except Exception:
        db.rollback(); raise


def update_enquiry_status(db: Session, enquiry_id: UUID, new_status: str, organization_id: UUID, user_id: UUID):
    enquiry = db.query(AdmissionEnquiry).filter(AdmissionEnquiry.id == enquiry_id, AdmissionEnquiry.organization_id == organization_id).with_for_update().first()
    if not enquiry:
        return None
    current = enquiry.status.upper(); target = new_status.upper()
    if target not in ADMISSION_TRANSITIONS.get(current, set()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid admission status transition: {current} -> {target}")
    enquiry.status = target
    try:
        log_action(db, organization_id, user_id, "UPDATE_STATUS", "ADMISSION_ENQUIRY", enquiry.id, old_values=current, new_values=target); db.commit(); db.refresh(enquiry); return enquiry
    except Exception:
        db.rollback(); raise
