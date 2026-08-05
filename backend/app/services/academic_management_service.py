from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import Branch, Grade, Section, Subject
from app.services.audit.audit_service import log_action


def _require_branch(db, branch_id, organization_id):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.organization_id == organization_id).first()
    if not branch: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch does not belong to this organization")
    return branch


def get_grades(db: Session, organization_id: UUID, branch_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(Grade).filter(Grade.organization_id == organization_id)
    if branch_id: query = query.filter(Grade.branch_id == branch_id)
    if search: query = query.filter(Grade.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_grade(db, grade_id, organization_id):
    return db.query(Grade).filter(Grade.id == grade_id, Grade.organization_id == organization_id).first()


def create_grade(db, grade_in, organization_id, user_id):
    _require_branch(db, grade_in.branch_id, organization_id)
    duplicate = db.query(Grade).filter(Grade.organization_id == organization_id, Grade.branch_id == grade_in.branch_id, Grade.name == grade_in.name).first()
    if duplicate: raise HTTPException(status_code=409, detail="Grade already exists in this branch")
    grade = Grade(**grade_in.model_dump(), organization_id=organization_id); db.add(grade); db.commit(); db.refresh(grade)
    log_action(db, organization_id, user_id, "CREATE", "GRADE", grade.id, new_values=str(grade_in.model_dump())); return grade


def get_sections(db, organization_id, branch_id=None, grade_id=None, skip=0, limit=100, search=None):
    query = db.query(Section).filter(Section.organization_id == organization_id)
    if branch_id: query = query.filter(Section.branch_id == branch_id)
    if grade_id: query = query.filter(Section.grade_id == grade_id)
    if search: query = query.filter(Section.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_section(db, section_id, organization_id):
    return db.query(Section).filter(Section.id == section_id, Section.organization_id == organization_id).first()


def create_section(db, section_in, organization_id, user_id):
    _require_branch(db, section_in.branch_id, organization_id)
    grade = get_grade(db, section_in.grade_id, organization_id)
    if not grade or grade.branch_id != section_in.branch_id: raise HTTPException(status_code=400, detail="Grade must belong to the selected branch")
    duplicate = db.query(Section).filter(Section.organization_id == organization_id, Section.branch_id == section_in.branch_id, Section.grade_id == section_in.grade_id, Section.name == section_in.name).first()
    if duplicate: raise HTTPException(status_code=409, detail="Section already exists for this grade")
    section = Section(**section_in.model_dump(), organization_id=organization_id); db.add(section); db.commit(); db.refresh(section)
    log_action(db, organization_id, user_id, "CREATE", "SECTION", section.id, new_values=str(section_in.model_dump())); return section


def get_subjects(db, organization_id, skip=0, limit=100, search=None):
    query = db.query(Subject).filter(Subject.organization_id == organization_id)
    if search: query = query.filter(Subject.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_subject(db, subject_id, organization_id):
    return db.query(Subject).filter(Subject.id == subject_id, Subject.organization_id == organization_id).first()


def create_subject(db, subject_in, organization_id, user_id):
    duplicate = db.query(Subject).filter(Subject.organization_id == organization_id, Subject.code == subject_in.code).first()
    if duplicate: raise HTTPException(status_code=409, detail="Subject code already exists")
    subject = Subject(**subject_in.model_dump(), organization_id=organization_id); db.add(subject); db.commit(); db.refresh(subject)
    log_action(db, organization_id, user_id, "CREATE", "SUBJECT", subject.id, new_values=str(subject_in.model_dump())); return subject


def _update(db, obj, payload, organization_id, user_id, resource):
    previous = str(obj.__dict__)
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(obj, field, value)
    db.commit(); db.refresh(obj); log_action(db, organization_id, user_id, "UPDATE", resource, obj.id, previous_values=previous, new_values=str(payload.model_dump(exclude_unset=True))); return obj


def update_grade(db, grade_id, grade_in, organization_id, user_id):
    grade = get_grade(db, grade_id, organization_id)
    if not grade: return None
    if getattr(grade_in, "branch_id", None): _require_branch(db, grade_in.branch_id, organization_id)
    return _update(db, grade, grade_in, organization_id, user_id, "GRADE")


def update_section(db, section_id, section_in, organization_id, user_id):
    section = get_section(db, section_id, organization_id)
    if not section: return None
    data = section_in.model_dump(exclude_unset=True); branch_id = data.get("branch_id", section.branch_id); grade_id = data.get("grade_id", section.grade_id)
    _require_branch(db, branch_id, organization_id); grade = get_grade(db, grade_id, organization_id)
    if not grade or grade.branch_id != branch_id: raise HTTPException(status_code=400, detail="Grade must belong to the selected branch")
    return _update(db, section, section_in, organization_id, user_id, "SECTION")


def update_subject(db, subject_id, subject_in, organization_id, user_id):
    subject = get_subject(db, subject_id, organization_id)
    return None if not subject else _update(db, subject, subject_in, organization_id, user_id, "SUBJECT")


def _delete(db, obj, organization_id, user_id, resource):
    if not obj: return False
    object_id = obj.id; db.delete(obj); db.commit(); log_action(db, organization_id, user_id, "DELETE", resource, object_id); return True


def delete_grade(db, grade_id, organization_id, user_id): return _delete(db, get_grade(db, grade_id, organization_id), organization_id, user_id, "GRADE")
def delete_section(db, section_id, organization_id, user_id): return _delete(db, get_section(db, section_id, organization_id), organization_id, user_id, "SECTION")
def delete_subject(db, subject_id, organization_id, user_id): return _delete(db, get_subject(db, subject_id, organization_id), organization_id, user_id, "SUBJECT")
