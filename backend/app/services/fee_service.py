from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import FeeType, FeeStructure, Grade, Invoice, Payment, Student
from app.schemas.fee import FeeTypeCreate, FeeStructureCreate, InvoiceCreate, PaymentCreate
from app.services.audit.audit_service import log_action


def _require_owned(db: Session, model, object_id: UUID, organization_id: UUID, label: str):
    obj = db.query(model).filter(model.id == object_id, model.organization_id == organization_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{label} is not available in this organization')
    return obj


def _commit_audited(db: Session, organization_id: UUID, user_id: UUID, action: str, entity: str, obj, payload=None):
    """Commit the business mutation and its audit event as one transaction."""
    try:
        db.flush()
        log_action(db, organization_id, user_id, action, entity, obj.id, new_values=str(payload) if payload is not None else None)
        db.commit()
        db.refresh(obj)
        return obj
    except Exception:
        db.rollback()
        raise


def get_student_branch_id(db, student_id, organization_id):
    return _require_owned(db, Student, student_id, organization_id, 'Student').branch_id


def get_invoice_branch_id(db, invoice_id, organization_id):
    return get_student_branch_id(db, _require_owned(db, Invoice, invoice_id, organization_id, 'Invoice').student_id, organization_id)


def get_fee_types(db, organization_id):
    return db.query(FeeType).filter(FeeType.organization_id == organization_id).order_by(FeeType.name).all()


def create_fee_type(db, type_in, organization_id, user_id):
    name = type_in.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail='Fee type name is required')
    if db.query(FeeType).filter(FeeType.organization_id == organization_id, FeeType.name == name).first():
        raise HTTPException(status_code=409, detail='Fee type already exists')
    ft = FeeType(name=name, organization_id=organization_id)
    db.add(ft)
    return _commit_audited(db, organization_id, user_id, 'CREATE', 'FEE_TYPE', ft, {'name': name})


def get_fee_structures(db, organization_id, grade_id=None):
    q = db.query(FeeStructure).filter(FeeStructure.organization_id == organization_id)
    return q.filter(FeeStructure.grade_id == grade_id).all() if grade_id else q.all()


def create_fee_structure(db, struct_in, organization_id, user_id):
    _require_owned(db, Grade, struct_in.grade_id, organization_id, 'Grade')
    _require_owned(db, FeeType, struct_in.fee_type_id, organization_id, 'Fee type')
    if struct_in.amount <= 0:
        raise HTTPException(status_code=422, detail='Fee structure amount must be greater than zero')
    if db.query(FeeStructure).filter(FeeStructure.organization_id == organization_id, FeeStructure.grade_id == struct_in.grade_id, FeeStructure.fee_type_id == struct_in.fee_type_id).first():
        raise HTTPException(status_code=409, detail='Fee structure already exists for this grade and fee type')
    fs = FeeStructure(**struct_in.model_dump(), organization_id=organization_id)
    db.add(fs)
    return _commit_audited(db, organization_id, user_id, 'CREATE', 'FEE_STRUCTURE', fs, struct_in.model_dump())


def get_invoices(db, organization_id, student_id=None, branch_ids=None):
    q = db.query(Invoice).filter(Invoice.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        q = q.join(Student, Student.id == Invoice.student_id).filter(Student.organization_id == organization_id, Student.branch_id.in_(branch_ids))
    if student_id:
        q = q.filter(Invoice.student_id == student_id)
    return q.order_by(Invoice.due_date.desc()).all()


def create_invoice(db, invoice_in, organization_id, user_id):
    _require_owned(db, Student, invoice_in.student_id, organization_id, 'Student')
    if invoice_in.amount_due <= 0:
        raise HTTPException(status_code=422, detail='Invoice amount must be greater than zero')
    inv = Invoice(**invoice_in.model_dump(), organization_id=organization_id)
    inv.status = 'UNPAID'
    db.add(inv)
    return _commit_audited(db, organization_id, user_id, 'CREATE', 'INVOICE', inv, invoice_in.model_dump())


def get_payments(db, organization_id, invoice_id=None, branch_ids=None):
    q = db.query(Payment).filter(Payment.organization_id == organization_id)
    if branch_ids is not None:
        if not branch_ids:
            return []
        q = q.join(Invoice, Invoice.id == Payment.invoice_id).join(Student, Student.id == Invoice.student_id).filter(Student.organization_id == organization_id, Student.branch_id.in_(branch_ids))
    if invoice_id:
        q = q.filter(Payment.invoice_id == invoice_id)
    return q.order_by(Payment.payment_date.desc()).all()


def create_payment(db, payment_in, organization_id, user_id):
    invoice = db.query(Invoice).filter(Invoice.id == payment_in.invoice_id, Invoice.organization_id == organization_id).with_for_update().first()
    if not invoice:
        raise HTTPException(status_code=400, detail='Invoice is not available in this organization')
    if invoice.status.upper() in {'CANCELLED', 'PAID'}:
        raise HTTPException(status_code=409, detail='Payments cannot be recorded against a closed invoice')
    paid = sum(row.amount_paid for row in db.query(Payment).filter(Payment.organization_id == organization_id, Payment.invoice_id == invoice.id).all())
    outstanding = invoice.amount_due - paid
    if outstanding <= 0:
        raise HTTPException(status_code=409, detail='Invoice has no outstanding balance')
    if payment_in.amount_paid <= 0:
        raise HTTPException(status_code=422, detail='Payment amount must be greater than zero')
    if payment_in.amount_paid > outstanding:
        raise HTTPException(status_code=409, detail='Payment exceeds the outstanding invoice amount')
    pay = Payment(**payment_in.model_dump(), organization_id=organization_id)
    db.add(pay)
    new_paid = paid + payment_in.amount_paid
    invoice.status = 'PAID' if new_paid == invoice.amount_due else 'PARTIALLY_PAID'
    return _commit_audited(db, organization_id, user_id, 'CREATE', 'PAYMENT', pay, payment_in.model_dump())
