from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.base import ExamType, Exam, ExamSchedule, ExamResult, Grade, Student, Subject
from app.schemas.exam import ExamResultCreate
from app.services.audit.audit_service import log_action

def _require_owned(db, model, object_id, organization_id, label):
    obj=db.query(model).filter(model.id==object_id,model.organization_id==organization_id).first()
    if not obj:raise HTTPException(status_code=400,detail=f"{label} does not belong to this organization")
    return obj

def get_exam_types(db,organization_id):return db.query(ExamType).filter(ExamType.organization_id==organization_id).all()
def create_exam_type(db,type_in,organization_id,user_id):
    et=ExamType(name=type_in.name,organization_id=organization_id);db.add(et);db.commit();db.refresh(et);log_action(db,organization_id,user_id,"CREATE","EXAM_TYPE",et.id,new_values=str(type_in.model_dump()));return et
def get_exams(db,organization_id,skip=0,limit=100):return db.query(Exam).filter(Exam.organization_id==organization_id).offset(skip).limit(limit).all()
def create_exam(db,exam_in,organization_id,user_id):
    _require_owned(db,ExamType,exam_in.exam_type_id,organization_id,"Exam type")
    if exam_in.end_date<exam_in.start_date:raise HTTPException(status_code=400,detail="Exam end date cannot be before start date")
    exam=Exam(**exam_in.model_dump(),organization_id=organization_id);db.add(exam);db.commit();db.refresh(exam);log_action(db,organization_id,user_id,"CREATE","EXAM",exam.id,new_values=str(exam_in.model_dump()));return exam
def delete_exam(db,exam_id,organization_id,user_id):
    exam=db.query(Exam).filter(Exam.id==exam_id,Exam.organization_id==organization_id).first()
    if not exam:return None
    db.delete(exam);db.commit();log_action(db,organization_id,user_id,"DELETE","EXAM",exam_id);return True
def get_exam_schedules(db,organization_id,exam_id=None):
    q=db.query(ExamSchedule).filter(ExamSchedule.organization_id==organization_id);return q.filter(ExamSchedule.exam_id==exam_id).all() if exam_id else q.all()
def create_exam_schedule(db,schedule_in,organization_id,user_id):
    exam=_require_owned(db,Exam,schedule_in.exam_id,organization_id,"Exam");_require_owned(db,Subject,schedule_in.subject_id,organization_id,"Subject");_require_owned(db,Grade,schedule_in.grade_id,organization_id,"Grade")
    if not exam.start_date<=schedule_in.date<=exam.end_date:raise HTTPException(status_code=400,detail="Exam schedule date must fall within the exam date range")
    duplicate=db.query(ExamSchedule).filter(ExamSchedule.organization_id==organization_id,ExamSchedule.exam_id==schedule_in.exam_id,ExamSchedule.subject_id==schedule_in.subject_id,ExamSchedule.grade_id==schedule_in.grade_id).first()
    if duplicate:raise HTTPException(status_code=409,detail="Exam schedule already exists for this subject and grade")
    obj=ExamSchedule(**schedule_in.model_dump(),organization_id=organization_id);db.add(obj);db.commit();db.refresh(obj);log_action(db,organization_id,user_id,"CREATE","EXAM_SCHEDULE",obj.id,new_values=str(schedule_in.model_dump()));return obj
def get_exam_results(db,organization_id,exam_id=None,student_id=None,branch_ids:set[UUID]|None=None):
    q=db.query(ExamResult).join(Student,Student.id==ExamResult.student_id).filter(ExamResult.organization_id==organization_id,Student.organization_id==organization_id)
    if branch_ids is not None:
        if not branch_ids:return []
        q=q.filter(Student.branch_id.in_(branch_ids))
    if exam_id:q=q.filter(ExamResult.exam_id==exam_id)
    if student_id:q=q.filter(ExamResult.student_id==student_id)
    return q.all()
def create_exam_result(db,result_in:ExamResultCreate,organization_id,user_id):
    _require_owned(db,Exam,result_in.exam_id,organization_id,"Exam");student=_require_owned(db,Student,result_in.student_id,organization_id,"Student");_require_owned(db,Subject,result_in.subject_id,organization_id,"Subject")
    if db.query(ExamResult).filter(ExamResult.organization_id==organization_id,ExamResult.exam_id==result_in.exam_id,ExamResult.student_id==result_in.student_id,ExamResult.subject_id==result_in.subject_id).first():raise HTTPException(status_code=409,detail="Exam result already exists")
    schedules=db.query(ExamSchedule).filter(ExamSchedule.organization_id==organization_id,ExamSchedule.exam_id==result_in.exam_id,ExamSchedule.subject_id==result_in.subject_id).all()
    if not schedules:raise HTTPException(status_code=400,detail="No exam schedule exists for this subject")
    schedule=next((r for r in schedules if r.grade_id==getattr(student,"grade_id",None)),None) if getattr(student,"grade_id",None) else (schedules[0] if len(schedules)==1 else None)
    if not schedule:raise HTTPException(status_code=400,detail="Unable to resolve an exam schedule for the student's grade")
    if result_in.marks_obtained>schedule.max_marks:raise HTTPException(status_code=400,detail="Marks obtained cannot exceed maximum marks")
    result=ExamResult(**result_in.model_dump(),organization_id=organization_id);db.add(result);db.commit();db.refresh(result);log_action(db,organization_id,user_id,"CREATE","EXAM_RESULT",result.id,new_values=str(result_in.model_dump()));return result
