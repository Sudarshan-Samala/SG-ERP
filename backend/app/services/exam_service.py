from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import ExamType, Exam, ExamSchedule, ExamResult, Grade, Student, Subject
from app.schemas.exam import ExamTypeCreate, ExamResultCreate
from app.services.audit.audit_service import log_action


def _require_owned(db: Session, model, object_id: UUID, organization_id: UUID, label: str):
    obj = db.query(model).filter(model.id == object_id, model.organization_id == organization_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} does not belong to this organization")
    return obj


def get_exam_types(db: Session, organization_id: UUID):
    return db.query(ExamType).filter(ExamType.organization_id == organization_id).all()


def create_exam_type(db: Session, type_in: ExamTypeCreate, organization_id: UUID, user_id: UUID):
    et = ExamType(name=type_in.name, organization_id=organization_id)
    db.add(et); db.commit(); db.refresh(et)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_TYPE", et.id, new_values=str(type_in.model_dump()))
    return et


def get_exams(db: Session, organization_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Exam).filter(Exam.organization_id == organization_id).offset(skip).limit(limit).all()


def create_exam(db: Session, exam_in, organization_id: UUID, user_id: UUID):
    _require_owned(db, ExamType, exam_in.exam_type_id, organization_id, "Exam type")
    exam = Exam(**exam_in.model_dump(), organization_id=organization_id)
    db.add(exam); db.commit(); db.refresh(exam)
    log_action(db, organization_id, user_id, "CREATE", "EXAM", exam.id, new_values=str(exam_in.model_dump()))
    return exam


def delete_exam(db: Session, exam_id: UUID, organization_id: UUID, user_id: UUID):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.organization_id == organization_id).first()
    if not exam: return None
    db.delete(exam); db.commit()
    log_action(db, organization_id, user_id, "DELETE", "EXAM", exam_id)
    return True


def get_exam_schedules(db: Session, organization_id: UUID, exam_id: Optional[UUID] = None):
    query = db.query(ExamSchedule).filter(ExamSchedule.organization_id == organization_id)
    if exam_id: query = query.filter(ExamSchedule.exam_id == exam_id)
    return query.all()


def create_exam_schedule(db: Session, schedule_in, organization_id: UUID, user_id: UUID):
    exam = _require_owned(db, Exam, schedule_in.exam_id, organization_id, "Exam")
    _require_owned(db, Subject, schedule_in.subject_id, organization_id, "Subject")
    _require_owned(db, Grade, schedule_in.grade_id, organization_id, "Grade")
    if schedule_in.date < exam.start_date or schedule_in.date > exam.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exam schedule date must fall within the exam date range")
    schedule = ExamSchedule(**schedule_in.model_dump(), organization_id=organization_id)
    db.add(schedule); db.commit(); db.refresh(schedule)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_SCHEDULE", schedule.id, new_values=str(schedule_in.model_dump()))
    return schedule


def get_exam_results(db: Session, organization_id: UUID, exam_id: Optional[UUID] = None, student_id: Optional[UUID] = None):
    query = db.query(ExamResult).filter(ExamResult.organization_id == organization_id)
    if exam_id: query = query.filter(ExamResult.exam_id == exam_id)
    if student_id: query = query.filter(ExamResult.student_id == student_id)
    return query.all()


def create_exam_result(db: Session, result_in: ExamResultCreate, organization_id: UUID, user_id: UUID):
    _require_owned(db, Exam, result_in.exam_id, organization_id, "Exam")
    _require_owned(db, Student, result_in.student_id, organization_id, "Student")
    _require_owned(db, Subject, result_in.subject_id, organization_id, "Subject")
    existing = db.query(ExamResult).filter(ExamResult.organization_id == organization_id, ExamResult.exam_id == result_in.exam_id, ExamResult.student_id == result_in.student_id, ExamResult.subject_id == result_in.subject_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exam result already exists")
    schedule = db.query(ExamSchedule).filter(ExamSchedule.organization_id == organization_id, ExamSchedule.exam_id == result_in.exam_id, ExamSchedule.subject_id == result_in.subject_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No exam schedule exists for this subject")
    if result_in.marks_obtained > schedule.max_marks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Marks obtained cannot exceed maximum marks")
    result = ExamResult(**result_in.model_dump(), organization_id=organization_id)
    db.add(result); db.commit(); db.refresh(result)
    log_action(db, organization_id, user_id, "CREATE", "EXAM_RESULT", result.id, new_values=str(result_in.model_dump()))
    return result
