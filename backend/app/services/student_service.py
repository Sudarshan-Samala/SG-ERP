from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import AcademicYear, Branch, Student
from app.schemas.student import StudentCreate, StudentStatusUpdate, StudentUpdate
from app.services.audit.audit_service import log_action

STUDENT_NUMBER_START = 100000
ALLOWED_STATUS_TRANSITIONS = {
    "ACTIVE": {"INACTIVE", "TRANSFERRED", "WITHDRAWN", "GRADUATED", "ARCHIVED"},
    "INACTIVE": {"ACTIVE", "TRANSFERRED", "WITHDRAWN", "ARCHIVED"},
    "TRANSFERRED": {"ARCHIVED"},
    "WITHDRAWN": {"ACTIVE", "ARCHIVED"},
    "GRADUATED": {"ALUMNI", "ARCHIVED"},
    "ALUMNI": {"ARCHIVED"},
    "ARCHIVED": set(),
}


def get_students(db: Session, organization_id: UUID, branch_ids: set[UUID] | None = None):
    query = db.query(Student).filter(Student.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        query = query.filter(Student.branch_id.in_(branch_ids))
    return query.order_by(Student.student_name).all()


def get_student(db: Session, student_id: UUID, organization_id: UUID):
    return db.query(Student).filter(Student.id == student_id, Student.organization_id == organization_id).first()


def get_student_by_number(db: Session, student_number: int, organization_id: UUID):
    return db.query(Student).filter(Student.student_number == student_number, Student.organization_id == organization_id).first()


def _validate_student_scope(db: Session, student_in: StudentCreate | StudentUpdate, organization_id: UUID):
    branch = db.query(Branch).filter(Branch.id == student_in.branch_id, Branch.organization_id == organization_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch is not available in this organization")
    academic_year = db.query(AcademicYear).filter(AcademicYear.id == student_in.academic_year_id, AcademicYear.organization_id == organization_id).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Academic year is not available in this organization")


def _ensure_admission_number_available(db: Session, admission_number: str, organization_id: UUID, exclude_id: UUID | None = None):
    query = db.query(Student).filter(Student.organization_id == organization_id, Student.admission_number == admission_number)
    if exclude_id:
        query = query.filter(Student.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admission number already exists")


def _next_student_number(db: Session, organization_id: UUID) -> int:
    current = db.query(func.max(Student.student_number)).filter(Student.organization_id == organization_id).scalar()
    return max(int(current or STUDENT_NUMBER_START - 1) + 1, STUDENT_NUMBER_START)


def create_student(db: Session, student_in: StudentCreate, organization_id: UUID, user_id: UUID):
    _validate_student_scope(db, student_in, organization_id)
    _ensure_admission_number_available(db, student_in.admission_number, organization_id)
    # The tenant-scoped unique constraint is the final concurrency guard. Retry
    # allocation if two admissions race for the same next permanent number.
    for attempt in range(3):
        student = Student(**student_in.model_dump(), organization_id=organization_id, student_number=_next_student_number(db, organization_id), status="ACTIVE")
        db.add(student)
        try:
            db.commit(); db.refresh(student)
            log_action(db, organization_id, user_id, "CREATE", "STUDENT", student.id, new_values=f"student_number={student.student_number}; {student_in.model_dump()}")
            return student
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student identity allocation conflict; retry request")
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student identity allocation conflict")


def update_student(db: Session, student_id: UUID, student_in: StudentUpdate, organization_id: UUID, user_id: UUID):
    student = get_student(db, student_id, organization_id)
    if not student:
        return None
    if student.status == "ARCHIVED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Archived students cannot be edited")
    _validate_student_scope(db, student_in, organization_id)
    _ensure_admission_number_available(db, student_in.admission_number, organization_id, student.id)
    previous_values = str(student.__dict__)
    for field, value in student_in.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    try:
        db.commit(); db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admission number already exists")
    log_action(db, organization_id, user_id, "UPDATE", "STUDENT", student.id, previous_values=previous_values, new_values=str(student_in.model_dump(exclude_unset=True)))
    return student


def change_student_status(db: Session, student_id: UUID, status_in: StudentStatusUpdate, organization_id: UUID, user_id: UUID):
    student = get_student(db, student_id, organization_id)
    if not student:
        return None
    if status_in.status == student.status:
        return student
    allowed = ALLOWED_STATUS_TRANSITIONS.get(student.status, set())
    if status_in.status not in allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid student status transition: {student.status} -> {status_in.status}")
    previous = student.status
    student.status = status_in.status
    student.status_changed_at = datetime.utcnow()
    db.commit(); db.refresh(student)
    log_action(db, organization_id, user_id, "STATUS_CHANGE", "STUDENT", student.id, previous_values=f"status={previous}", new_values=f"status={student.status}; reason={status_in.reason}")
    return student


def archive_student(db: Session, student_id: UUID, reason: str, organization_id: UUID, user_id: UUID):
    return change_student_status(db, student_id, StudentStatusUpdate(status="ARCHIVED", reason=reason), organization_id, user_id)


def delete_student(db: Session, student_id: UUID, organization_id: UUID, user_id: UUID):
    """Permanent deletion is intentionally disabled for issued student identities."""
    student = get_student(db, student_id, organization_id)
    if not student:
        return False
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permanent student deletion is disabled. Archive the student to preserve institutional identity and history.")
