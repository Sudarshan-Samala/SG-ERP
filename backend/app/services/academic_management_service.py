from sqlalchemy.orm import Session
from app.models.base import Grade, Section, Subject
from app.schemas.academic_management import GradeCreate, SectionCreate, SubjectCreate
from app.services.audit.audit_service import log_action
from typing import Optional
from uuid import UUID

# Grade
def get_grades(db: Session, organization_id: UUID, branch_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(Grade).filter(Grade.organization_id == organization_id)
    if branch_id:
        query = query.filter(Grade.branch_id == branch_id)
    if search:
        query = query.filter(Grade.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def get_grade(db: Session, grade_id: UUID, organization_id: UUID):
    return db.query(Grade).filter(Grade.id == grade_id, Grade.organization_id == organization_id).first()

def create_grade(db: Session, grade_in: GradeCreate, organization_id: UUID, user_id: UUID):
    grade = Grade(**grade_in.dict(), organization_id=organization_id)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    log_action(db, organization_id, user_id, "CREATE", "GRADE", grade.id, new_values=str(grade_in.dict()))
    return grade

def update_grade(db: Session, grade_id: UUID, grade_in, organization_id: UUID, user_id: UUID):
    grade = get_grade(db, grade_id, organization_id)
    if not grade: return None
    previous = str(grade.__dict__)
    for field, value in grade_in.dict(exclude_unset=True).items():
        setattr(grade, field, value)
    db.commit()
    db.refresh(grade)
    log_action(db, organization_id, user_id, "UPDATE", "GRADE", grade.id, previous_values=previous, new_values=str(grade_in.dict(exclude_unset=True)))
    return grade

def delete_grade(db: Session, grade_id: UUID, organization_id: UUID, user_id: UUID):
    grade = get_grade(db, grade_id, organization_id)
    if not grade: return False
    db.delete(grade)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "GRADE", grade_id)
    return True

# Section
def get_sections(db: Session, organization_id: UUID, branch_id: Optional[UUID] = None, grade_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(Section).filter(Section.organization_id == organization_id)
    if branch_id:
        query = query.filter(Section.branch_id == branch_id)
    if grade_id:
        query = query.filter(Section.grade_id == grade_id)
    if search:
        query = query.filter(Section.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def get_section(db: Session, section_id: UUID, organization_id: UUID):
    return db.query(Section).filter(Section.id == section_id, Section.organization_id == organization_id).first()

def create_section(db: Session, section_in: SectionCreate, organization_id: UUID, user_id: UUID):
    section = Section(**section_in.dict(), organization_id=organization_id)
    db.add(section)
    db.commit()
    db.refresh(section)
    log_action(db, organization_id, user_id, "CREATE", "SECTION", section.id, new_values=str(section_in.dict()))
    return section

def update_section(db: Session, section_id: UUID, section_in, organization_id: UUID, user_id: UUID):
    section = get_section(db, section_id, organization_id)
    if not section: return None
    previous = str(section.__dict__)
    for field, value in section_in.dict(exclude_unset=True).items():
        setattr(section, field, value)
    db.commit()
    db.refresh(section)
    log_action(db, organization_id, user_id, "UPDATE", "SECTION", section.id, previous_values=previous, new_values=str(section_in.dict(exclude_unset=True)))
    return section

def delete_section(db: Session, section_id: UUID, organization_id: UUID, user_id: UUID):
    section = get_section(db, section_id, organization_id)
    if not section: return False
    db.delete(section)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "SECTION", section_id)
    return True

# Subject
def get_subjects(db: Session, organization_id: UUID, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(Subject).filter(Subject.organization_id == organization_id)
    if search:
        query = query.filter(Subject.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def get_subject(db: Session, subject_id: UUID, organization_id: UUID):
    return db.query(Subject).filter(Subject.id == subject_id, Subject.organization_id == organization_id).first()

def create_subject(db: Session, subject_in: SubjectCreate, organization_id: UUID, user_id: UUID):
    subject = Subject(**subject_in.dict(), organization_id=organization_id)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    log_action(db, organization_id, user_id, "CREATE", "SUBJECT", subject.id, new_values=str(subject_in.dict()))
    return subject

def update_subject(db: Session, subject_id: UUID, subject_in, organization_id: UUID, user_id: UUID):
    subject = get_subject(db, subject_id, organization_id)
    if not subject: return None
    previous = str(subject.__dict__)
    for field, value in subject_in.dict(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    log_action(db, organization_id, user_id, "UPDATE", "SUBJECT", subject.id, previous_values=previous, new_values=str(subject_in.dict(exclude_unset=True)))
    return subject

def delete_subject(db: Session, subject_id: UUID, organization_id: UUID, user_id: UUID):
    subject = get_subject(db, subject_id, organization_id)
    if not subject: return False
    db.delete(subject)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "SUBJECT", subject_id)
    return True
