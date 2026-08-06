import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.core.database import get_db
from app.models.base import Attendance as AttendanceModel, Organization, Student, User
from app.schemas.attendance import Attendance, AttendanceCreate
from app.services.attendance_service import get_attendance

router = APIRouter()


class BulkAttendanceRequest(BaseModel):
    branch_id: UUID
    date: datetime
    records: list[dict] = Field(min_length=1, max_length=200)


def _attendance_query(db, org_id, current_user, branch_id=None, student_id=None, date=None):
    allowed = None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:
        enforce_branch_access(current_user, branch_id)
    query = db.query(AttendanceModel).filter(AttendanceModel.organization_id == org_id)
    if allowed is not None:
        query = query.filter(AttendanceModel.branch_id.in_(allowed)) if allowed else query.filter(False)
    if branch_id:
        query = query.filter(AttendanceModel.branch_id == branch_id)
    if student_id:
        student = db.query(Student).filter(Student.id == student_id, Student.organization_id == org_id).first()
        if student:
            enforce_branch_access(current_user, student.branch_id)
        query = query.filter(AttendanceModel.student_id == student_id)
    if date:
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(AttendanceModel.date >= day_start, AttendanceModel.date < day_start + timedelta(days=1))
    return query.order_by(AttendanceModel.date.desc())


@router.get('/', response_model=List[Attendance])
def read_attendance(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), branch_id: Optional[UUID] = None, student_id: Optional[UUID] = None, date: Optional[datetime] = None, skip: int = 0, limit: int = 100, current_user: User = Depends(require_permission('attendance.read'))):
    page_limit = min(max(limit, 1), 500)
    return _attendance_query(db, current_org.id, current_user, branch_id, student_id, date).offset(max(skip, 0)).limit(page_limit).all()


@router.get('/export.csv')
def attendance_export(branch_id: Optional[UUID] = None, date: Optional[datetime] = None, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.read'))):
    rows = _attendance_query(db, current_org.id, current_user, branch_id, None, date).all()
    student_ids = {row.student_id for row in rows}
    students = {student.id: student for student in db.query(Student).filter(Student.organization_id == current_org.id, Student.id.in_(student_ids)).all()} if student_ids else {}
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['date', 'admission_number', 'student_name', 'branch_id', 'status'])
    for row in rows:
        student = students.get(row.student_id)
        writer.writerow([row.date.date().isoformat(), student.admission_number if student else '', student.student_name if student else '', str(row.branch_id), row.status])
    suffix = date.date().isoformat() if date else 'all'
    return Response(content=out.getvalue(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="attendance-{suffix}.csv"'})


@router.get('/exceptions')
def attendance_exceptions(date: datetime, branch_id: Optional[UUID] = None, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.read'))):
    allowed = None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:
        enforce_branch_access(current_user, branch_id)
    students = db.query(Student).filter(Student.organization_id == current_org.id)
    if branch_id:
        students = students.filter(Student.branch_id == branch_id)
    elif allowed is not None:
        students = students.filter(Student.branch_id.in_(allowed)) if allowed else students.filter(False)
    student_rows = students.all()
    marked_ids = {row.student_id for row in _attendance_query(db, current_org.id, current_user, branch_id, None, date).all()}
    missing = [{'student_id': student.id, 'student_name': student.student_name, 'admission_number': student.admission_number, 'branch_id': student.branch_id} for student in student_rows if student.id not in marked_ids]
    return {'date': date.date().isoformat(), 'students': len(student_rows), 'marked': len(marked_ids), 'missing_count': len(missing), 'missing': missing}


@router.post('/bulk')
def bulk_attendance(payload: BulkAttendanceRequest, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.mark'))):
    enforce_branch_access(current_user, payload.branch_id)
    now = datetime.now(timezone.utc) if payload.date.tzinfo else datetime.now()
    if payload.date.date() > now.date():
        raise HTTPException(status_code=400, detail='Attendance cannot be marked for a future date')
    seen = set()
    validated = []
    for item in payload.records:
        try:
            sid = UUID(str(item.get('student_id')))
            status_value = str(item.get('status', '')).upper()
        except Exception as exc:
            raise HTTPException(status_code=400, detail='Invalid student attendance record') from exc
        if sid in seen:
            raise HTTPException(status_code=400, detail='Duplicate student in bulk attendance request')
        seen.add(sid)
        if status_value not in {'PRESENT', 'ABSENT', 'LATE'}:
            raise HTTPException(status_code=400, detail='Invalid attendance status')
        student = db.query(Student).filter(Student.id == sid, Student.organization_id == current_org.id, Student.branch_id == payload.branch_id).first()
        if not student:
            raise HTTPException(status_code=400, detail='Student does not belong to the selected branch')
        validated.append((sid, status_value))
    day_start = payload.date.replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.query(AttendanceModel.student_id).filter(AttendanceModel.organization_id == current_org.id, AttendanceModel.student_id.in_(seen), AttendanceModel.date >= day_start, AttendanceModel.date < day_start + timedelta(days=1)).first()
    if existing:
        raise HTTPException(status_code=409, detail='Attendance has already been marked for one or more students on this date.')
    for sid, status_value in validated:
        db.add(AttendanceModel(branch_id=payload.branch_id, student_id=sid, date=payload.date, status=status_value, organization_id=current_org.id))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {'created': len(validated)}


@router.post('/', response_model=Attendance)
def create_attendance_endpoint(att_in: AttendanceCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.mark'))):
    student = db.query(Student).filter(Student.id == att_in.student_id, Student.organization_id == current_org.id).first()
    if not student:
        raise HTTPException(status_code=400, detail='Student does not belong to this organization')
    if student.branch_id != att_in.branch_id:
        raise HTTPException(status_code=400, detail='Student does not belong to the selected branch')
    enforce_branch_access(current_user, student.branch_id)
    from app.services.attendance_service import create_attendance
    return create_attendance(db, att_in, current_org.id, current_user.id)
