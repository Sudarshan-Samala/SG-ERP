from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission, enforce_branch_access, accessible_branch_ids
from app.services.student_service import get_students, create_student, update_student, delete_student
from app.schemas.student import Student, StudentCreate
from app.models.base import Organization, User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[Student])
def read_students(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), branch_id: Optional[UUID] = None, current_user: User = Depends(require_permission("students.read"))):
    if branch_id:
        enforce_branch_access(current_user, branch_id)
        return get_students(db, organization_id=current_org.id, branch_id=branch_id)
    students = get_students(db, organization_id=current_org.id)
    if current_user.is_superuser: return students
    allowed = accessible_branch_ids(current_user)
    return [student for student in students if student.branch_id in allowed]

@router.post("/", response_model=Student)
def create_student_endpoint(student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.create"))):
    enforce_branch_access(current_user, student_in.branch_id)
    return create_student(db, student_in, current_org.id, current_user.id)

@router.put("/{student_id}", response_model=Student)
def update_student_endpoint(student_id: UUID, student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    enforce_branch_access(current_user, student_in.branch_id)
    existing = next((s for s in get_students(db, organization_id=current_org.id) if s.id == student_id), None)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enforce_branch_access(current_user, existing.branch_id)
    student = update_student(db, student_id, student_in, current_org.id, current_user.id)
    if not student: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_endpoint(student_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    existing = next((s for s in get_students(db, organization_id=current_org.id) if s.id == student_id), None)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enforce_branch_access(current_user, existing.branch_id)
    if not delete_student(db, student_id, current_org.id, current_user.id): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return None
