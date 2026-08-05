from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import accessible_branch_ids, get_current_organization, require_permission
from app.core.database import get_db
from app.models.base import Attendance, Invoice, Organization, Payment, Student, User

router = APIRouter()

@router.get('/overview')
def overview(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission('reports.read'))):
    branches = None if current_user.is_superuser else accessible_branch_ids(current_user)
    students = db.query(Student).filter(Student.organization_id == current_org.id)
    attendance = db.query(Attendance).filter(Attendance.organization_id == current_org.id)
    invoices = db.query(Invoice).join(Student, Student.id == Invoice.student_id).filter(Invoice.organization_id == current_org.id)
    payments = db.query(Payment).join(Invoice, Invoice.id == Payment.invoice_id).join(Student, Student.id == Invoice.student_id).filter(Payment.organization_id == current_org.id)
    if branches is not None:
        if branches:
            students = students.filter(Student.branch_id.in_(branches)); attendance = attendance.filter(Attendance.branch_id.in_(branches)); invoices = invoices.filter(Student.branch_id.in_(branches)); payments = payments.filter(Student.branch_id.in_(branches))
        else:
            students = students.filter(False); attendance = attendance.filter(False); invoices = invoices.filter(False); payments = payments.filter(False)
    total_attendance = attendance.count(); present = attendance.filter(Attendance.status == 'PRESENT').count()
    invoiced = int(invoices.with_entities(func.coalesce(func.sum(Invoice.amount_due), 0)).scalar() or 0)
    collected = int(payments.with_entities(func.coalesce(func.sum(Payment.amount_paid), 0)).scalar() or 0)
    return {'students': students.count(), 'attendance_records': total_attendance, 'attendance_rate': round(present / total_attendance * 100, 1) if total_attendance else None, 'fees_invoiced': invoiced, 'fees_collected': collected, 'fees_balance': max(invoiced-collected, 0)}
