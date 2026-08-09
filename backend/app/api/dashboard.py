from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import accessible_branch_ids, get_current_user
from app.core.database import get_db
from app.models.base import Attendance, Employee, Invoice, Payment, Student, Ticket, User

router = APIRouter()


def _permissions(user: User) -> set[str]:
    return {permission.name for role in user.roles for permission in role.permissions}


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org_id = current_user.organization_id
    permissions = _permissions(current_user)
    branch_ids = None if current_user.is_superuser else accessible_branch_ids(current_user)
    result: dict[str, int] = {}

    if current_user.is_superuser or "students.read" in permissions:
        query = db.query(Student).filter(Student.organization_id == org_id)
        if branch_ids is not None:
            query = query.filter(Student.branch_id.in_(branch_ids)) if branch_ids else query.filter(False)
        result["students"] = query.count()

    if current_user.is_superuser or "hr.read" in permissions:
        result["employees"] = db.query(Employee).filter(Employee.organization_id == org_id).count()

    if current_user.is_superuser or "helpdesk.read" in permissions:
        query = db.query(Ticket).filter(Ticket.organization_id == org_id, Ticket.status.in_(["OPEN", "IN_PROGRESS"]))
        if not current_user.is_superuser and "helpdesk.manage" not in permissions:
            query = query.filter(Ticket.requester_id == current_user.id)
        result["open_tickets"] = query.count()
        result["high_priority_tickets"] = query.filter(Ticket.priority.in_(["HIGH", "CRITICAL"])).count()

    if current_user.is_superuser or "attendance.read" in permissions:
        start = datetime.combine(datetime.utcnow().date(), time.min)
        end = datetime.combine(datetime.utcnow().date(), time.max)
        query = db.query(Attendance).filter(Attendance.organization_id == org_id, Attendance.date >= start, Attendance.date <= end)
        if branch_ids is not None:
            query = query.filter(Attendance.branch_id.in_(branch_ids)) if branch_ids else query.filter(False)
        result["attendance_marked_today"] = query.count()
        result["present_today"] = query.filter(Attendance.status == "PRESENT").count()

    if current_user.is_superuser or "fees.read" in permissions:
        invoice_query = db.query(Invoice).join(Student, Student.id == Invoice.student_id).filter(Invoice.organization_id == org_id)
        payment_query = db.query(Payment).join(Invoice, Invoice.id == Payment.invoice_id).join(Student, Student.id == Invoice.student_id).filter(Payment.organization_id == org_id)
        if branch_ids is not None:
            if branch_ids:
                invoice_query = invoice_query.filter(Student.branch_id.in_(branch_ids))
                payment_query = payment_query.filter(Student.branch_id.in_(branch_ids))
            else:
                invoice_query = invoice_query.filter(False)
                payment_query = payment_query.filter(False)
        result["outstanding_fees"] = int(invoice_query.filter(Invoice.status.in_(["UNPAID", "OVERDUE", "PARTIALLY_PAID"])).with_entities(func.coalesce(func.sum(Invoice.amount_due), 0)).scalar() or 0)
        result["fees_collected"] = int(payment_query.with_entities(func.coalesce(func.sum(Payment.amount_paid), 0)).scalar() or 0)

    return result
