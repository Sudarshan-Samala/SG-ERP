from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.exam_service import get_exam_types, create_exam_type, get_exams, create_exam, delete_exam, get_exam_schedules, create_exam_schedule, get_exam_results, create_exam_result
from app.schemas.exam import ExamType, ExamTypeCreate, Exam, ExamCreate, ExamSchedule, ExamScheduleCreate, ExamResult, ExamResultCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/types", response_model=List[ExamType])
def read_exam_types(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("exam.read"))): return get_exam_types(db, current_org.id)

@router.post("/types", response_model=ExamType)
def create_exam_type_endpoint(type_in: ExamTypeCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("exam.manage"))): return create_exam_type(db, type_in, current_org.id, current_user.id)

@router.get("/", response_model=List[Exam])
def read_exams(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), skip: int = 0, limit: int = 100, _: User = Depends(require_permission("exam.read"))): return get_exams(db, current_org.id, skip, limit)

@router.post("/", response_model=Exam)
def create_exam_endpoint(exam_in: ExamCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("exam.manage"))): return create_exam(db, exam_in, current_org.id, current_user.id)

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_endpoint(exam_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("exam.manage"))):
    if not delete_exam(db, exam_id, current_org.id, current_user.id): raise HTTPException(status_code=404, detail="Exam not found")
    return None

@router.get("/schedules", response_model=List[ExamSchedule])
def read_schedules(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), exam_id: Optional[UUID] = None, _: User = Depends(require_permission("exam.read"))): return get_exam_schedules(db, current_org.id, exam_id)

@router.post("/schedules", response_model=ExamSchedule)
def create_schedule_endpoint(schedule_in: ExamScheduleCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("exam.schedule.manage"))): return create_exam_schedule(db, schedule_in, current_org.id, current_user.id)

@router.get("/results", response_model=List[ExamResult])
def read_results(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), exam_id: Optional[UUID] = None, student_id: Optional[UUID] = None, _: User = Depends(require_permission("exam.result.read"))): return get_exam_results(db, current_org.id, exam_id, student_id)

@router.post("/results", response_model=ExamResult)
def create_result_endpoint(result_in: ExamResultCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("exam.result.create"))): return create_exam_result(db, result_in, current_org.id, current_user.id)
