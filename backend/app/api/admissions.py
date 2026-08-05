from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Literal
from app.core.database import get_db
from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.services.admission_service import get_enquiries, create_enquiry, update_enquiry_status
from app.schemas.admission import AdmissionEnquiry, AdmissionEnquiryCreate
from app.models.base import AcademicYear, AdmissionEnquiry as AdmissionEnquiryModel, Branch, Organization, Student, User
from app.services.audit.audit_service import log_action

router = APIRouter()

class AdmissionConversion(BaseModel):
    admission_number: str = Field(min_length=1, max_length=50)
    date_of_birth: datetime
    gender: Literal['male','female','other']

@router.get('/enquiries', response_model=List[AdmissionEnquiry])
def read_enquiries(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('admissions.read'))):
    return get_enquiries(db,current_org.id,None if current_user.is_superuser else accessible_branch_ids(current_user))

@router.post('/enquiries', response_model=AdmissionEnquiry)
def create_enquiry_endpoint(enquiry_in:AdmissionEnquiryCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('admissions.manage'))):
    enforce_branch_access(current_user,enquiry_in.branch_id);return create_enquiry(db,enquiry_in,current_org.id)

@router.patch('/enquiries/{enquiry_id}/status/{new_status}', response_model=AdmissionEnquiry)
def change_enquiry_status(enquiry_id:UUID,new_status:str,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('admissions.manage'))):
    enquiry=db.query(AdmissionEnquiryModel).filter(AdmissionEnquiryModel.id==enquiry_id,AdmissionEnquiryModel.organization_id==current_org.id).first()
    if not enquiry:raise HTTPException(status_code=404,detail='Admission enquiry not found')
    enforce_branch_access(current_user,enquiry.branch_id);return update_enquiry_status(db,enquiry_id,new_status,current_org.id)

@router.post('/enquiries/{enquiry_id}/convert', status_code=status.HTTP_201_CREATED)
def convert_enquiry(enquiry_id:UUID,payload:AdmissionConversion,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('students.create'))):
    enquiry=db.query(AdmissionEnquiryModel).filter(AdmissionEnquiryModel.id==enquiry_id,AdmissionEnquiryModel.organization_id==current_org.id).with_for_update().first()
    if not enquiry:raise HTTPException(status_code=404,detail='Admission enquiry not found')
    enforce_branch_access(current_user,enquiry.branch_id)
    if enquiry.status.upper()!='SELECTED':raise HTTPException(status_code=409,detail='Only selected enquiries can be converted to students')
    if not db.query(Branch).filter(Branch.id==enquiry.branch_id,Branch.organization_id==current_org.id).first() or not db.query(AcademicYear).filter(AcademicYear.id==enquiry.academic_year_id,AcademicYear.organization_id==current_org.id).first():raise HTTPException(status_code=409,detail='Admission branch or academic year is no longer available')
    number=payload.admission_number.strip().upper()
    if db.query(Student).filter(Student.organization_id==current_org.id,Student.admission_number==number).first():raise HTTPException(status_code=409,detail='Admission number already exists')
    student=Student(organization_id=current_org.id,branch_id=enquiry.branch_id,academic_year_id=enquiry.academic_year_id,admission_number=number,student_name=enquiry.student_name.strip(),date_of_birth=payload.date_of_birth,gender=payload.gender,email=enquiry.email.strip().lower() if enquiry.email else None,phone=enquiry.phone.strip() if enquiry.phone else None)
    db.add(student);enquiry.status='ADMITTED'
    try:db.commit();db.refresh(student)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Unable to convert enquiry; admission number may already exist') from exc
    log_action(db,current_org.id,current_user.id,'CONVERT','ADMISSION_ENQUIRY',enquiry.id,new_values=f'student_id={student.id}')
    return {'student_id':student.id,'admission_number':student.admission_number,'student_name':student.student_name,'status':'ADMITTED'}
