from sqlalchemy.orm import Session
from app.models.base import Student
from app.schemas.student import StudentCreate
from uuid import UUID

def get_students(db: Session, organization_id: UUID):
    return db.query(Student).filter(Student.organization_id == organization_id).all()

def get_student(db: Session, student_id: UUID, organization_id: UUID):
    return db.query(Student).filter(Student.id == student_id, Student.organization_id == organization_id).first()

def create_student(db: Session, student_in: StudentCreate, organization_id: UUID, user_id: UUID):
    student = Student(
        **student_in.dict(),
        organization_id=organization_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    log_action(db, organization_id, user_id, "CREATE", "STUDENT", student.id, new_values=str(student_in.dict()))
    return student

def update_student(db: Session, student_id: UUID, student_in: StudentCreate, organization_id: UUID, user_id: UUID):
    student = get_student(db, student_id, organization_id)
    if not student:
        return None
    previous_values = str(student.__dict__)
    for field, value in student_in.dict(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    log_action(db, organization_id, user_id, "UPDATE", "STUDENT", student.id, previous_values=previous_values, new_values=str(student_in.dict(exclude_unset=True)))
    return student

def delete_student(db: Session, student_id: UUID, organization_id: UUID, user_id: UUID):
    student = get_student(db, student_id, organization_id)
    if not student:
        return False
    db.delete(student)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "STUDENT", student_id)
    return True
