from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import AcademicYear, Branch, Student
from app.schemas.student import StudentCreate
from app.services.audit.audit_service import log_action

def get_students(db: Session, organization_id: UUID, branch_ids=None):
    query=db.query(Student).filter(Student.organization_id==organization_id)
    if branch_ids is not None:
        if not branch_ids:return []
        query=query.filter(Student.branch_id.in_(branch_ids))
    return query.order_by(Student.student_name).all()
def get_student(db:Session,student_id:UUID,organization_id:UUID):return db.query(Student).filter(Student.id==student_id,Student.organization_id==organization_id).first()
def _validate_student_scope(db,student_in,organization_id):
    branch=db.query(Branch).filter(Branch.id==student_in.branch_id,Branch.organization_id==organization_id,Branch.is_active==True).first()
    if not branch:raise HTTPException(status_code=400,detail='Branch is not active or available in this organization')
    year=db.query(AcademicYear).filter(AcademicYear.id==student_in.academic_year_id,AcademicYear.organization_id==organization_id).first()
    if not year:raise HTTPException(status_code=400,detail='Academic year is not available in this organization')
def _ensure_admission_number_available(db,admission_number,organization_id,exclude_id=None):
    normalized=admission_number.strip().upper();query=db.query(Student).filter(Student.organization_id==organization_id,Student.admission_number==normalized)
    if exclude_id:query=query.filter(Student.id!=exclude_id)
    if query.first():raise HTTPException(status_code=409,detail='Admission number already exists')
    return normalized
def create_student(db,student_in,organization_id,user_id):
    _validate_student_scope(db,student_in,organization_id);number=_ensure_admission_number_available(db,student_in.admission_number,organization_id);values=student_in.model_dump();values['admission_number']=number;values['student_name']=student_in.student_name.strip();student=Student(**values,organization_id=organization_id);db.add(student)
    try:db.flush();log_action(db,organization_id,user_id,'CREATE','STUDENT',student.id,new_values=str(values));db.commit();db.refresh(student);return student
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Admission number already exists') from exc
    except Exception:db.rollback();raise
def update_student(db,student_id,student_in,organization_id,user_id):
    student=get_student(db,student_id,organization_id)
    if not student:return None
    _validate_student_scope(db,student_in,organization_id);number=_ensure_admission_number_available(db,student_in.admission_number,organization_id,student.id);previous=str(student.__dict__);values=student_in.model_dump(exclude_unset=True);values['admission_number']=number;values['student_name']=student_in.student_name.strip()
    for field,value in values.items():setattr(student,field,value)
    try:db.flush();log_action(db,organization_id,user_id,'UPDATE','STUDENT',student.id,previous_values=previous,new_values=str(values));db.commit();db.refresh(student);return student
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Admission number already exists') from exc
    except Exception:db.rollback();raise
def delete_student(db,student_id,organization_id,user_id):
    student=get_student(db,student_id,organization_id)
    if not student:return False
    try:db.delete(student);log_action(db,organization_id,user_id,'DELETE','STUDENT',student_id);db.commit();return True
    except Exception:db.rollback();raise
