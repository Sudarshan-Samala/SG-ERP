from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.student_service import get_students, create_student, update_student, delete_student
from app.schemas.student import Student, StudentCreate
from app.models.base import Organization, User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[Student])
def read_students(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("students.read"))):
    return get_students(db, organization_id=current_org.id)

@router.post("/", response_model=Student)
def create_student_endpoint(student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.create"))):
    return create_student(db, student_in, current_org.id, current_user.id)

@router.put("/{student_id}", response_model=Student)
def update_student_endpoint(student_id: UUID, student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    student = update_student(db, student_id, student_in, current_org.id, current_user.id)
    if not student: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_endpoint(student_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    if not delete_student(db, student_id, current_org.id, current_user.id): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return None
