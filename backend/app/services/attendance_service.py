from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Attendance, Branch, Student
from app.schemas.attendance import AttendanceCreate
from app.services.audit.audit_service import log_action


def get_attendance(db, organization_id, branch_id=None, student_id=None, date=None, skip=0, limit=100):
    query = db.query(Attendance).filter(Attendance.organization_id == organization_id)
    if branch_id: query = query.filter(Attendance.branch_id == branch_id)
    if student_id: query = query.filter(Attendance.student_id == student_id)
    if date:
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0); query = query.filter(Attendance.date >= day_start, Attendance.date < day_start + timedelta(days=1))
    return query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()


def create_attendance(db, att_in, organization_id, user_id):
    branch = db.query(Branch).filter(Branch.id == att_in.branch_id, Branch.organization_id == organization_id).first()
    if not branch: raise HTTPException(status_code=400, detail="Branch is not available in this organization")
    student = db.query(Student).filter(Student.id == att_in.student_id, Student.organization_id == organization_id).first()
    if not student: raise HTTPException(status_code=400, detail="Student is not available in this organization")
    if student.branch_id != att_in.branch_id: raise HTTPException(status_code=400, detail="Student does not belong to the selected branch")
    attendance_date = att_in.date
    now = datetime.now(timezone.utc) if attendance_date.tzinfo else datetime.now()
    if attendance_date.date() > now.date(): raise HTTPException(status_code=400, detail="Attendance cannot be marked for a future date")
    day_start = attendance_date.replace(hour=0, minute=0, second=0, microsecond=0); day_end = day_start + timedelta(days=1)
    existing = db.query(Attendance).filter(Attendance.organization_id == organization_id, Attendance.student_id == att_in.student_id, Attendance.date >= day_start, Attendance.date < day_end).first()
    if existing: raise HTTPException(status_code=409, detail="Attendance has already been marked for this student on this date.")
    att = Attendance(**att_in.model_dump(), organization_id=organization_id); db.add(att)
    try: db.commit(); db.refresh(att)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Attendance has already been marked for this student on this date.") from exc
    log_action(db, organization_id, user_id, "CREATE", "ATTENDANCE", att.id, new_values=str(att_in.model_dump())); return att
