from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import FeeType, FeeStructure, Grade, Invoice, Payment, Student
from app.schemas.fee import FeeTypeCreate, FeeStructureCreate, InvoiceCreate, PaymentCreate
from app.services.audit.audit_service import log_action


def _require_owned(db: Session, model, object_id: UUID, organization_id: UUID, label: str):
    obj = db.query(model).filter(model.id == object_id, model.organization_id == organization_id).first()
    if not obj: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} is not available in this organization")
    return obj


def get_student_branch_id(db: Session, student_id: UUID, organization_id: UUID) -> UUID:
    return _require_owned(db, Student, student_id, organization_id, "Student").branch_id


def get_invoice_branch_id(db: Session, invoice_id: UUID, organization_id: UUID) -> UUID:
    invoice = _require_owned(db, Invoice, invoice_id, organization_id, "Invoice")
    return get_student_branch_id(db, invoice.student_id, organization_id)


def get_fee_types(db, organization_id): return db.query(FeeType).filter(FeeType.organization_id == organization_id).order_by(FeeType.name).all()


def create_fee_type(db, type_in: FeeTypeCreate, organization_id, user_id):
    duplicate = db.query(FeeType).filter(FeeType.organization_id == organization_id, FeeType.name == type_in.name).first()
    if duplicate: raise HTTPException(status_code=409, detail="Fee type already exists")
    ft = FeeType(name=type_in.name, organization_id=organization_id); db.add(ft); db.commit(); db.refresh(ft); log_action(db, organization_id, user_id, "CREATE", "FEE_TYPE", ft.id, new_values=str(type_in.model_dump())); return ft


def get_fee_structures(db, organization_id, grade_id=None):
    query = db.query(FeeStructure).filter(FeeStructure.organization_id == organization_id)
    return query.filter(FeeStructure.grade_id == grade_id).all() if grade_id else query.all()


def create_fee_structure(db, struct_in: FeeStructureCreate, organization_id, user_id):
    _require_owned(db, Grade, struct_in.grade_id, organization_id, "Grade"); _require_owned(db, FeeType, struct_in.fee_type_id, organization_id, "Fee type")
    duplicate = db.query(FeeStructure).filter(FeeStructure.organization_id == organization_id, FeeStructure.grade_id == struct_in.grade_id, FeeStructure.fee_type_id == struct_in.fee_type_id).first()
    if duplicate: raise HTTPException(status_code=409, detail="Fee structure already exists for this grade and fee type")
    fs = FeeStructure(**struct_in.model_dump(), organization_id=organization_id); db.add(fs); db.commit(); db.refresh(fs); log_action(db, organization_id, user_id, "CREATE", "FEE_STRUCTURE", fs.id, new_values=str(struct_in.model_dump())); return fs


def get_invoices(db, organization_id, student_id=None, branch_ids: set[UUID] | None = None):
    query = db.query(Invoice).filter(Invoice.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids: return []
        query = query.join(Student, Student.id == Invoice.student_id).filter(Student.organization_id == organization_id, Student.branch_id.in_(branch_ids))
    if student_id: query = query.filter(Invoice.student_id == student_id)
    return query.order_by(Invoice.due_date.desc()).all()


def create_invoice(db, invoice_in: InvoiceCreate, organization_id, user_id):
    _require_owned(db, Student, invoice_in.student_id, organization_id, "Student")
    inv = Invoice(**invoice_in.model_dump(), organization_id=organization_id); db.add(inv); db.commit(); db.refresh(inv); log_action(db, organization_id, user_id, "CREATE", "INVOICE", inv.id, new_values=str(invoice_in.model_dump())); return inv


def get_payments(db, organization_id, invoice_id=None, branch_ids: set[UUID] | None = None):
    query = db.query(Payment).filter(Payment.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids: return []
        query = query.join(Invoice, Invoice.id == Payment.invoice_id).join(Student, Student.id == Invoice.student_id).filter(Student.organization_id == organization_id, Student.branch_id.in_(branch_ids))
    if invoice_id: query = query.filter(Payment.invoice_id == invoice_id)
    return query.order_by(Payment.payment_date.desc()).all()


def create_payment(db, payment_in: PaymentCreate, organization_id, user_id):
    invoice = db.query(Invoice).filter(Invoice.id == payment_in.invoice_id, Invoice.organization_id == organization_id).with_for_update().first()
    if not invoice: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice is not available in this organization")
    if invoice.status in {"cancelled", "paid"}: raise HTTPException(status_code=409, detail="Payments cannot be recorded against a closed invoice")
    paid = sum(row.amount_paid for row in db.query(Payment).filter(Payment.organization_id == organization_id, Payment.invoice_id == invoice.id).all())
    outstanding = invoice.amount_due - paid
    if payment_in.amount_paid <= 0: raise HTTPException(status_code=422, detail="Payment amount must be greater than zero")
    if payment_in.amount_paid > outstanding: raise HTTPException(status_code=409, detail="Payment exceeds the outstanding invoice amount")
    pay = Payment(**payment_in.model_dump(), organization_id=organization_id); db.add(pay)
    new_paid = paid + payment_in.amount_paid
    invoice.status = "paid" if new_paid == invoice.amount_due else "partially_paid"
    db.commit(); db.refresh(pay); log_action(db, organization_id, user_id, "CREATE", "PAYMENT", pay.id, new_values=str(payment_in.model_dump())); return pay
