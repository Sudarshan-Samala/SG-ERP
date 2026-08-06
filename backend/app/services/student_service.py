from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import AcademicYear, Branch, Student
from app.schemas.student import StudentCreate
from app.services.audit.audit_service import log_action


def get_students(db: Session, organization_id: UUID, branch_ids: set[UUID] | None = None):
    query = db.query(Student).filter(Student.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        query = query.filter(Student.branch_id.in_(branch_ids))
    return query.order_by(Student.student_name).all()


def get_student(db: Session, student_id: UUID, organization_id: UUID):
    return (
        db.query(Student)
        .filter(Student.id == student_id, Student.organization_id == organization_id)
        .first()
    )


def _validate_student_scope(db: Session, student_in: StudentCreate, organization_id: UUID):
    branch = (
        db.query(Branch)
        .filter(Branch.id == student_in.branch_id, Branch.organization_id == organization_id)
        .first()
    )
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch is not available in this organization",
        )
    academic_year = (
        db.query(AcademicYear)
        .filter(
            AcademicYear.id == student_in.academic_year_id,
            AcademicYear.organization_id == organization_id,
        )
        .first()
    )
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Academic year is not available in this organization",
        )


def _ensure_admission_number_available(
    db: Session,
    admission_number: str,
    organization_id: UUID,
    exclude_id: UUID | None = None,
):
    query = db.query(Student).filter(
        Student.organization_id == organization_id,
        Student.admission_number == admission_number,
    )
    if exclude_id:
        query = query.filter(Student.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admission number already exists",
        )


def create_student(
    db: Session,
    student_in: StudentCreate,
    organization_id: UUID,
    user_id: UUID,
):
    _validate_student_scope(db, student_in, organization_id)
    _ensure_admission_number_available(db, student_in.admission_number, organization_id)
    student = Student(**student_in.model_dump(), organization_id=organization_id)
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admission number already exists",
        )
    log_action(
        db,
        organization_id,
        user_id,
        "CREATE",
        "STUDENT",
        student.id,
        new_values=str(student_in.model_dump()),
    )
    return student


def update_student(
    db: Session,
    student_id: UUID,
    student_in: StudentCreate,
    organization_id: UUID,
    user_id: UUID,
):
    student = get_student(db, student_id, organization_id)
    if not student:
        return None
    _validate_student_scope(db, student_in, organization_id)
    _ensure_admission_number_available(db, student_in.admission_number, organization_id, student.id)
    previous_values = str(student.__dict__)
    for field, value in student_in.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admission number already exists",
        )
    log_action(
        db,
        organization_id,
        user_id,
        "UPDATE",
        "STUDENT",
        student.id,
        previous_values=previous_values,
        new_values=str(student_in.model_dump(exclude_unset=True)),
    )
    return student


def delete_student(
    db: Session,
    student_id: UUID,
    organization_id: UUID,
    user_id: UUID,
):
    student = get_student(db, student_id, organization_id)
    if not student:
        return False
    db.delete(student)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "STUDENT", student_id)
    return True
