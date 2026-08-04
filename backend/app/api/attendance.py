from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.attendance_service import get_attendance, create_attendance
from app.schemas.attendance import Attendance, AttendanceCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/", response_model=List[Attendance])
def read_attendance(
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_organization),
    branch_id: Optional[UUID] = None,
    student_id: Optional[UUID] = None,
    date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    return get_attendance(
        db, 
        organization_id=current_org.id, 
        branch_id=branch_id, 
        student_id=student_id, 
        date=date,
        skip=skip,
        limit=limit
    )

@router.post("/", response_model=Attendance)
def create_attendance_endpoint(
    att_in: AttendanceCreate, 
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user)
):
    return create_attendance(db, att_in, organization_id=current_org.id, user_id=current_user.id)
