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


def get_invoices(db, organization_id, student_id=None):
    query = db.query(Invoice).filter(Invoice.organization_id == organization_id)
    return query.filter(Invoice.student_id == student_id).all() if student_id else query.all()


def create_invoice(db, invoice_in: InvoiceCreate, organization_id, user_id):
    _require_owned(db, Student, invoice_in.student_id, organization_id, "Student")
    inv = Invoice(**invoice_in.model_dump(), organization_id=organization_id); db.add(inv); db.commit(); db.refresh(inv); log_action(db, organization_id, user_id, "CREATE", "INVOICE", inv.id, new_values=str(invoice_in.model_dump())); return inv


def get_payments(db, organization_id, invoice_id=None):
    query = db.query(Payment).filter(Payment.organization_id == organization_id)
    return query.filter(Payment.invoice_id == invoice_id).all() if invoice_id else query.all()


def create_payment(db, payment_in: PaymentCreate, organization_id, user_id):
    invoice = _require_owned(db, Invoice, payment_in.invoice_id, organization_id, "Invoice")
    if invoice.status in {"cancelled", "paid"}: raise HTTPException(status_code=409, detail="Payments cannot be recorded against a closed invoice")
    paid = sum(row.amount_paid for row in db.query(Payment).filter(Payment.organization_id == organization_id, Payment.invoice_id == invoice.id).all())
    outstanding = invoice.amount_due - paid
    if payment_in.amount_paid > outstanding: raise HTTPException(status_code=409, detail="Payment exceeds the outstanding invoice amount")
    pay = Payment(**payment_in.model_dump(), organization_id=organization_id); db.add(pay)
    new_paid = paid + payment_in.amount_paid
    invoice.status = "paid" if new_paid == invoice.amount_due else "partially_paid"
    db.commit(); db.refresh(pay); log_action(db, organization_id, user_id, "CREATE", "PAYMENT", pay.id, new_values=str(payment_in.model_dump())); return pay
