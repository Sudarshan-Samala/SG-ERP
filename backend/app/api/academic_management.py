from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.academic_management_service import (
    get_grades, create_grade, update_grade, delete_grade,
    get_sections, create_section, update_section, delete_section,
    get_subjects, create_subject, update_subject, delete_subject
)
from app.schemas.academic_management import (
    Grade, GradeCreate,
    Section, SectionCreate,
    Subject, SubjectCreate
)
from app.models.base import Organization, User
from uuid import UUID

router = APIRouter()

# Grades
@router.get("/grades", response_model=List[Grade])
def read_grades(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    branch_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    return get_grades(db, organization_id=current_org.id, branch_id=branch_id, skip=skip, limit=limit, search=search)

@router.post("/grades", response_model=Grade)
def create_grade_endpoint(grade_in: GradeCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_grade(db, grade_in, current_org.id, current_user.id)

@router.put("/grades/{grade_id}", response_model=Grade)
def update_grade_endpoint(grade_id: UUID, grade_in: GradeCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    grade = update_grade(db, grade_id, grade_in, current_org.id, current_user.id)
    if not grade: raise HTTPException(status_code=404, detail="Grade not found")
    return grade

@router.delete("/grades/{grade_id}")
def delete_grade_endpoint(grade_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    if not delete_grade(db, grade_id, current_org.id, current_user.id): raise HTTPException(status_code=404, detail="Grade not found")
    return {"message": "Grade deleted"}

# Sections
@router.get("/sections", response_model=List[Section])
def read_sections(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    branch_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    return get_sections(db, organization_id=current_org.id, branch_id=branch_id, grade_id=grade_id, skip=skip, limit=limit, search=search)

@router.post("/sections", response_model=Section)
def create_section_endpoint(section_in: SectionCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_section(db, section_in, current_org.id, current_user.id)

@router.put("/sections/{section_id}", response_model=Section)
def update_section_endpoint(section_id: UUID, section_in: SectionCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    section = update_section(db, section_id, section_in, current_org.id, current_user.id)
    if not section: raise HTTPException(status_code=404, detail="Section not found")
    return section

@router.delete("/sections/{section_id}")
def delete_section_endpoint(section_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    if not delete_section(db, section_id, current_org.id, current_user.id): raise HTTPException(status_code=404, detail="Section not found")
    return {"message": "Section deleted"}

# Subjects
@router.get("/subjects", response_model=List[Subject])
def read_subjects(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    return get_subjects(db, organization_id=current_org.id, skip=skip, limit=limit, search=search)

@router.post("/subjects", response_model=Subject)
def create_subject_endpoint(subject_in: SubjectCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_subject(db, subject_in, current_org.id, current_user.id)

@router.put("/subjects/{subject_id}", response_model=Subject)
def update_subject_endpoint(subject_id: UUID, subject_in: SubjectCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    subject = update_subject(db, subject_id, subject_in, current_org.id, current_user.id)
    if not subject: raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.delete("/subjects/{subject_id}")
def delete_subject_endpoint(subject_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    if not delete_subject(db, subject_id, current_org.id, current_user.id): raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted"}
