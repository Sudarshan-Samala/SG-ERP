from datetime import date, datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.core.database import get_db
from app.models.base import Attendance, Invoice, Organization, Payment, Student, User

router = APIRouter()

def _date_window(from_date: date | None, to_date: date | None):
    if from_date and to_date and to_date < from_date:
        raise HTTPException(status_code=422, detail='to_date cannot be before from_date')
    start = datetime.combine(from_date, datetime.min.time()) if from_date else None
    end = datetime.combine(to_date + timedelta(days=1), datetime.min.time()) if to_date else None
    return start, end

@router.get('/overview')
def overview(branch_id: UUID | None = None, from_date: date | None = None, to_date: date | None = None, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('reports.read'))):
    branches = None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:
        enforce_branch_access(current_user, branch_id)
    start, end = _date_window(from_date, to_date)
    students = db.query(Student).filter(Student.organization_id == current_org.id)
    attendance = db.query(Attendance).filter(Attendance.organization_id == current_org.id)
    invoices = db.query(Invoice).join(Student, Student.id == Invoice.student_id).filter(Invoice.organization_id == current_org.id)
    payments = db.query(Payment).join(Invoice, Invoice.id == Payment.invoice_id).join(Student, Student.id == Invoice.student_id).filter(Payment.organization_id == current_org.id)
    if branches is not None:
        if branches:
            students = students.filter(Student.branch_id.in_(branches)); attendance = attendance.filter(Attendance.branch_id.in_(branches)); invoices = invoices.filter(Student.branch_id.in_(branches)); payments = payments.filter(Student.branch_id.in_(branches))
        else:
            students = students.filter(False); attendance = attendance.filter(False); invoices = invoices.filter(False); payments = payments.filter(False)
    if branch_id:
        students = students.filter(Student.branch_id == branch_id); attendance = attendance.filter(Attendance.branch_id == branch_id); invoices = invoices.filter(Student.branch_id == branch_id); payments = payments.filter(Student.branch_id == branch_id)
    if start:
        attendance = attendance.filter(Attendance.date >= start); invoices = invoices.filter(Invoice.due_date >= start); payments = payments.filter(Payment.payment_date >= start)
    if end:
        attendance = attendance.filter(Attendance.date < end); invoices = invoices.filter(Invoice.due_date < end); payments = payments.filter(Payment.payment_date < end)
    total_attendance = attendance.count(); present = attendance.filter(Attendance.status == 'PRESENT').count()
    invoiced = int(invoices.with_entities(func.coalesce(func.sum(Invoice.amount_due), 0)).scalar() or 0)
    collected = int(payments.with_entities(func.coalesce(func.sum(Payment.amount_paid), 0)).scalar() or 0)
    return {'students': students.count(), 'attendance_records': total_attendance, 'attendance_rate': round(present / total_attendance * 100, 1) if total_attendance else None, 'fees_invoiced': invoiced, 'fees_collected': collected, 'fees_balance': max(invoiced-collected, 0), 'collection_rate': round(collected / invoiced * 100, 1) if invoiced else None, 'filters': {'branch_id': branch_id, 'from_date': from_date, 'to_date': to_date}}
