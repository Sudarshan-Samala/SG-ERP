from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import enforce_branch_access, get_current_organization, require_permission
from app.services.student_service import get_student, get_students, create_student, update_student, delete_student
from app.schemas.student import Student, StudentCreate
from app.models.base import Attendance, Exam, ExamResult, Invoice, Organization, Payment, Subject, User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[Student])
def read_students(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("students.read"))):
    return get_students(db, organization_id=current_org.id)

@router.get("/{student_id}/profile")
def read_student_profile(student_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.read"))):
    student = get_student(db, student_id, current_org.id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enforce_branch_access(current_user, student.branch_id)
    permissions = {p.name for r in current_user.roles for p in r.permissions}
    payload = {"student": student, "attendance": None, "fees": None, "results": []}
    if current_user.is_superuser or "attendance.read" in permissions:
        total = db.query(Attendance).filter(Attendance.organization_id == current_org.id, Attendance.student_id == student.id).count()
        present = db.query(Attendance).filter(Attendance.organization_id == current_org.id, Attendance.student_id == student.id, Attendance.status == "PRESENT").count()
        payload["attendance"] = {"total_days": total, "present_days": present, "percentage": round((present / total * 100), 1) if total else None}
    if current_user.is_superuser or "fees.read" in permissions:
        invoices = db.query(Invoice).filter(Invoice.organization_id == current_org.id, Invoice.student_id == student.id).all()
        invoice_ids = [i.id for i in invoices]
        paid = int(db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).filter(Payment.organization_id == current_org.id, Payment.invoice_id.in_(invoice_ids)).scalar() or 0) if invoice_ids else 0
        due = sum(i.amount_due for i in invoices)
        payload["fees"] = {"invoiced": due, "paid": paid, "balance": max(due - paid, 0)}
    if current_user.is_superuser or "exams.read" in permissions:
        rows = db.query(ExamResult, Exam.name, Subject.name).join(Exam, Exam.id == ExamResult.exam_id).join(Subject, Subject.id == ExamResult.subject_id).filter(ExamResult.organization_id == current_org.id, ExamResult.student_id == student.id).order_by(Exam.start_date.desc(), Subject.name).limit(50).all()
        payload["results"] = [{"exam": exam_name, "subject": subject_name, "marks": result.marks_obtained} for result, exam_name, subject_name in rows]
    return payload

@router.post("/", response_model=Student)
def create_student_endpoint(student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.create"))):
    enforce_branch_access(current_user, student_in.branch_id)
    return create_student(db, student_in, current_org.id, current_user.id)

@router.put("/{student_id}", response_model=Student)
def update_student_endpoint(student_id: UUID, student_in: StudentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    existing = get_student(db, student_id, current_org.id)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enforce_branch_access(current_user, existing.branch_id); enforce_branch_access(current_user, student_in.branch_id)
    return update_student(db, student_id, student_in, current_org.id, current_user.id)

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_endpoint(student_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("students.manage"))):
    existing = get_student(db, student_id, current_org.id)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enforce_branch_access(current_user, existing.branch_id)
    delete_student(db, student_id, current_org.id, current_user.id)
    return None
