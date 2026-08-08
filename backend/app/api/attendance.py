import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.core.database import get_db
from app.models.base import Attendance as AttendanceModel, Organization, Student, User
from app.models.workflow_extensions import AttendanceCorrection
from app.schemas.attendance import Attendance, AttendanceCreate

router = APIRouter()

class BulkAttendanceRecord(BaseModel):
    student_id: UUID
    status: Literal['PRESENT', 'ABSENT', 'LATE']

class BulkAttendanceRequest(BaseModel):
    branch_id: UUID
    date: datetime
    records: list[BulkAttendanceRecord] = Field(min_length=1, max_length=200)

class CorrectionRequest(BaseModel):
    requested_status: Literal['PRESENT', 'ABSENT', 'LATE']
    reason: str = Field(min_length=5, max_length=1000)

class CorrectionDecision(BaseModel):
    decision: Literal['APPROVE', 'REJECT']

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
        if not student:
            return query.filter(False)
        enforce_branch_access(current_user, student.branch_id)
        query = query.filter(AttendanceModel.student_id == student_id)
    if date:
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(AttendanceModel.date >= day_start, AttendanceModel.date < day_start + timedelta(days=1))
    return query.order_by(AttendanceModel.date.desc(), AttendanceModel.id.desc())

def _constraint_name(exc: IntegrityError):
    orig = getattr(exc, 'orig', None)
    diag = getattr(orig, 'diag', None)
    return getattr(diag, 'constraint_name', None)

def _csv_chunk(rows, students, include_header=False):
    out = io.StringIO()
    writer = csv.writer(out)
    if include_header:
        writer.writerow(['date', 'admission_number', 'student_name', 'branch_id', 'status'])
    for row in rows:
        student = students.get(row.student_id)
        writer.writerow([row.date.date().isoformat(), student.admission_number if student else '', student.student_name if student else '', str(row.branch_id), row.status])
    return out.getvalue()

@router.get('/', response_model=List[Attendance])
def read_attendance(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), branch_id: Optional[UUID] = None, student_id: Optional[UUID] = None, date: Optional[datetime] = None, skip: int = 0, limit: int = 100, current_user: User = Depends(require_permission('attendance.read'))):
    page_limit = min(max(limit, 1), 500)
    return _attendance_query(db, current_org.id, current_user, branch_id, student_id, date).offset(max(skip, 0)).limit(page_limit).all()

@router.get('/export.csv')
def attendance_export(branch_id: Optional[UUID] = None, date: Optional[datetime] = None, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.read'))):
    query = _attendance_query(db, current_org.id, current_user, branch_id, None, date)
    def generate_csv():
        batch_size, offset, first_batch = 1000, 0, True
        while True:
            rows = query.offset(offset).limit(batch_size).all()
            if not rows:
                if first_batch:
                    yield _csv_chunk([], {}, include_header=True)
                break
            student_ids = {row.student_id for row in rows}
            students = {student.id: student for student in db.query(Student).filter(Student.organization_id == current_org.id, Student.id.in_(student_ids)).all()}
            yield _csv_chunk(rows, students, include_header=first_batch)
            first_batch = False
            offset += len(rows)
            if len(rows) < batch_size:
                break
    suffix = date.date().isoformat() if date else 'all'
    return StreamingResponse(generate_csv(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="attendance-{suffix}.csv"'})

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

@router.get('/corrections')
def list_corrections(status: Optional[Literal['PENDING', 'APPROVED', 'REJECTED']] = None, branch_id: Optional[UUID] = None, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.read'))):
    allowed = None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:
        enforce_branch_access(current_user, branch_id)
    query = db.query(AttendanceCorrection, AttendanceModel, Student).join(AttendanceModel, AttendanceModel.id == AttendanceCorrection.attendance_id).join(Student, Student.id == AttendanceModel.student_id).filter(AttendanceCorrection.organization_id == current_org.id)
    if allowed is not None:
        query = query.filter(AttendanceModel.branch_id.in_(allowed)) if allowed else query.filter(False)
    if branch_id:
        query = query.filter(AttendanceModel.branch_id == branch_id)
    if status:
        query = query.filter(AttendanceCorrection.status == status)
    rows = query.order_by(AttendanceCorrection.created_at.desc()).limit(500).all()
    return [{'id': c.id, 'attendance_id': a.id, 'student_id': s.id, 'student_name': s.student_name, 'admission_number': s.admission_number, 'branch_id': a.branch_id, 'date': a.date, 'current_status': a.status, 'requested_status': c.requested_status, 'reason': c.reason, 'status': c.status, 'requested_by': c.requested_by, 'reviewed_by': c.reviewed_by, 'reviewed_at': c.reviewed_at, 'created_at': c.created_at} for c, a, s in rows]

@router.post('/{attendance_id}/correction', status_code=201)
def request_correction(attendance_id: UUID, payload: CorrectionRequest, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.correction.request'))):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id, AttendanceModel.organization_id == current_org.id).with_for_update().first()
    if not attendance:
        raise HTTPException(status_code=404, detail='Attendance record not found')
    enforce_branch_access(current_user, attendance.branch_id)
    if attendance.status == payload.requested_status:
        raise HTTPException(status_code=422, detail='Requested status is the same as the current status')
    existing = db.query(AttendanceCorrection).filter(AttendanceCorrection.organization_id == current_org.id, AttendanceCorrection.attendance_id == attendance.id, AttendanceCorrection.status == 'PENDING').first()
    if existing:
        raise HTTPException(status_code=409, detail='A correction request is already pending for this attendance record')
    correction = AttendanceCorrection(organization_id=current_org.id, attendance_id=attendance.id, requested_status=payload.requested_status, reason=payload.reason.strip(), requested_by=current_user.id, status='PENDING')
    db.add(correction)
    try:
        db.commit(); db.refresh(correction)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail='A correction request already exists for this attendance record') from exc
    return {'id': correction.id, 'attendance_id': correction.attendance_id, 'requested_status': correction.requested_status, 'status': correction.status, 'reason': correction.reason, 'created_at': correction.created_at}

@router.patch('/corrections/{correction_id}')
def decide_correction(correction_id: UUID, payload: CorrectionDecision, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.correction.approve'))):
    correction = db.query(AttendanceCorrection).filter(AttendanceCorrection.id == correction_id, AttendanceCorrection.organization_id == current_org.id).with_for_update().first()
    if not correction:
        raise HTTPException(status_code=404, detail='Correction request not found')
    if correction.status != 'PENDING':
        raise HTTPException(status_code=409, detail='Correction request has already been decided')
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == correction.attendance_id, AttendanceModel.organization_id == current_org.id).with_for_update().first()
    if not attendance:
        raise HTTPException(status_code=404, detail='Attendance record no longer exists')
    enforce_branch_access(current_user, attendance.branch_id)
    correction.status = 'APPROVED' if payload.decision == 'APPROVE' else 'REJECTED'
    correction.reviewed_by = current_user.id
    correction.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if correction.status == 'APPROVED':
        attendance.status = correction.requested_status
    try:
        db.commit(); db.refresh(correction)
    except Exception:
        db.rollback(); raise
    return {'id': correction.id, 'attendance_id': correction.attendance_id, 'status': correction.status, 'attendance_status': attendance.status, 'reviewed_by': correction.reviewed_by, 'reviewed_at': correction.reviewed_at}

@router.post('/bulk')
def bulk_attendance(payload: BulkAttendanceRequest, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('attendance.mark'))):
    enforce_branch_access(current_user, payload.branch_id)
    now = datetime.now(timezone.utc) if payload.date.tzinfo else datetime.now()
    if payload.date.date() > now.date():
        raise HTTPException(status_code=400, detail='Attendance cannot be marked for a future date')
    seen = set()
    for item in payload.records:
        if item.student_id in seen:
            raise HTTPException(status_code=400, detail='Duplicate student in bulk attendance request')
        seen.add(item.student_id)
    students = {student.id: student for student in db.query(Student).filter(Student.id.in_(seen), Student.organization_id == current_org.id, Student.branch_id == payload.branch_id).all()}
    if len(students) != len(seen):
        raise HTTPException(status_code=400, detail='Student does not belong to the selected branch')
    day_start = payload.date.replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.query(AttendanceModel.student_id).filter(AttendanceModel.organization_id == current_org.id, AttendanceModel.student_id.in_(seen), AttendanceModel.date >= day_start, AttendanceModel.date < day_start + timedelta(days=1)).first()
    if existing:
        raise HTTPException(status_code=409, detail='Attendance has already been marked for one or more students on this date.')
    for item in payload.records:
        db.add(AttendanceModel(branch_id=payload.branch_id, student_id=item.student_id, date=payload.date, status=item.status, organization_id=current_org.id))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if _constraint_name(exc) == 'uq_attendance_student_daily':
            raise HTTPException(status_code=409, detail='Attendance has already been marked for one or more students on this date.') from exc
        raise
    except Exception:
        db.rollback(); raise
    return {'created': len(payload.records)}

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
