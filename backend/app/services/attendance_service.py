from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Attendance
from app.schemas.attendance import AttendanceCreate
from app.services.audit.audit_service import log_action


def get_attendance(
    db: Session,
    organization_id: UUID,
    branch_id: Optional[UUID] = None,
    student_id: Optional[UUID] = None,
    date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(Attendance).filter(
        Attendance.organization_id == organization_id
    )

    if branch_id:
        query = query.filter(Attendance.branch_id == branch_id)

    if student_id:
        query = query.filter(Attendance.student_id == student_id)

    if date:
        day_start = date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        day_end = day_start + timedelta(days=1)

        query = query.filter(
            Attendance.date >= day_start,
            Attendance.date < day_end,
        )

    return (
        query
        .order_by(Attendance.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_attendance(
    db: Session,
    att_in: AttendanceCreate,
    organization_id: UUID,
    user_id: UUID,
):
    day_start = att_in.date.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    day_end = day_start + timedelta(days=1)

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.organization_id == organization_id,
            Attendance.student_id == att_in.student_id,
            Attendance.date >= day_start,
            Attendance.date < day_end,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been marked for this student on this date.",
        )

    att = Attendance(
        **att_in.model_dump(),
        organization_id=organization_id,
    )

    db.add(att)

    try:
        db.commit()
        db.refresh(att)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been marked for this student on this date.",
        )

    log_action(
        db,
        organization_id,
        user_id,
        "CREATE",
        "ATTENDANCE",
        att.id,
        new_values=str(att_in.model_dump()),
    )

    return att
