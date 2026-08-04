from sqlalchemy.orm import Session
from app.models.base import ExamType, Exam, ExamSchedule, ExamResult
from app.schemas.exam import ExamTypeCreate, ExamResultCreate
from app.services.audit.audit_service import log_action
from uuid import UUID
from typing import Optional

# ExamType
def get_exam_types(db: Session, organization_id: UUID):
    return db.query(ExamType).filter(ExamType.organization_id == organization_id).all()

def create_exam_type(db: Session, type_in: ExamTypeCreate, organization_id: UUID, user_id: UUID):
    et = ExamType(name=type_in.name, organization_id=organization_id)
    db.add(et)
    db.commit()
    db.refresh(et)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_TYPE", et.id, new_values=str(type_in.model_dump()))
    return et

# Exam
def get_exams(db: Session, organization_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Exam).filter(Exam.organization_id == organization_id).offset(skip).limit(limit).all()

def create_exam(db: Session, exam_in, organization_id: UUID, user_id: UUID):
    exam = Exam(**exam_in.model_dump(), organization_id=organization_id)
    db.add(exam)
    db.commit()
    db.refresh(exam)
    log_action(db, organization_id, user_id, "CREATE", "EXAM", exam.id, new_values=str(exam_in.model_dump()))
    return exam

def delete_exam(db: Session, exam_id: UUID, organization_id: UUID, user_id: UUID):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.organization_id == organization_id).first()
    if not exam:
        return None
    db.delete(exam)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "EXAM", exam_id)
    return True

# ExamSchedule
def get_exam_schedules(db: Session, organization_id: UUID, exam_id: Optional[UUID] = None):
    query = db.query(ExamSchedule).filter(ExamSchedule.organization_id == organization_id)
    if exam_id:
        query = query.filter(ExamSchedule.exam_id == exam_id)
    return query.all()

def create_exam_schedule(db: Session, schedule_in, organization_id: UUID, user_id: UUID):
    schedule = ExamSchedule(**schedule_in.model_dump(), organization_id=organization_id)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_SCHEDULE", schedule.id, new_values=str(schedule_in.model_dump()))
    return schedule

# ExamResult
def get_exam_results(db: Session, organization_id: UUID, exam_id: Optional[UUID] = None, student_id: Optional[UUID] = None):
    query = db.query(ExamResult).filter(ExamResult.organization_id == organization_id)
    if exam_id:
        query = query.filter(ExamResult.exam_id == exam_id)
    if student_id:
        query = query.filter(ExamResult.student_id == student_id)
    return query.all()

def create_exam_result(db: Session, result_in: ExamResultCreate, organization_id: UUID, user_id: UUID):
    # 1. Check for duplicate
    existing = db.query(ExamResult).filter(
        ExamResult.organization_id == organization_id,
        ExamResult.exam_id == result_in.exam_id,
        ExamResult.student_id == result_in.student_id,
        ExamResult.subject_id == result_in.subject_id
    ).first()
    if existing:
        return None 

    # 2. Check marks
    schedule = db.query(ExamSchedule).filter(
        ExamSchedule.organization_id == organization_id,
        ExamSchedule.exam_id == result_in.exam_id,
        ExamSchedule.subject_id == result_in.subject_id
    ).first()
    
    if not schedule or result_in.marks_obtained > schedule.max_marks:
        return False

    result = ExamResult(**result_in.model_dump(), organization_id=organization_id)
    db.add(result)
    db.commit()
    db.refresh(result)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_RESULT", result.id, new_values=str(result_in.model_dump()))
    return result
