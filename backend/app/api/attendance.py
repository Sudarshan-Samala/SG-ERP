from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission, enforce_branch_access, accessible_branch_ids
from app.services.attendance_service import get_attendance, create_attendance
from app.schemas.attendance import Attendance, AttendanceCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/", response_model=List[Attendance])
def read_attendance(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), branch_id: Optional[UUID] = None, student_id: Optional[UUID] = None, date: Optional[datetime] = None, skip: int = 0, limit: int = 100, current_user: User = Depends(require_permission("attendance.read"))):
    if branch_id: enforce_branch_access(current_user, branch_id)
    rows = get_attendance(db, organization_id=current_org.id, branch_id=branch_id, student_id=student_id, date=date, skip=skip, limit=min(max(limit, 1), 500))
    if current_user.is_superuser or branch_id: return rows
    allowed = accessible_branch_ids(current_user)
    return [row for row in rows if row.branch_id in allowed]

@router.post("/", response_model=Attendance)
def create_attendance_endpoint(att_in: AttendanceCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("attendance.mark"))):
    enforce_branch_access(current_user, att_in.branch_id)
    return create_attendance(db, att_in, organization_id=current_org.id, user_id=current_user.id)
