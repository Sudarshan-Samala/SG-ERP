from sqlalchemy.orm import Session
from app.models.base import FeeType, FeeStructure, Invoice, Payment
from app.schemas.fee import FeeTypeCreate, FeeStructureCreate, InvoiceCreate, PaymentCreate
from app.services.audit.audit_service import log_action
from uuid import UUID
from typing import Optional

# FeeType
def get_fee_types(db: Session, organization_id: UUID):
    return db.query(FeeType).filter(FeeType.organization_id == organization_id).all()

def create_fee_type(db: Session, type_in: FeeTypeCreate, organization_id: UUID, user_id: UUID):
    ft = FeeType(name=type_in.name, organization_id=organization_id)
    db.add(ft)
    db.commit()
    db.refresh(ft)
    log_action(db, organization_id, user_id, "CREATE", "FEE_TYPE", ft.id, new_values=str(type_in.model_dump()))
    return ft

# FeeStructure
def get_fee_structures(db: Session, organization_id: UUID, grade_id: Optional[UUID] = None):
    query = db.query(FeeStructure).filter(FeeStructure.organization_id == organization_id)
    if grade_id:
        query = query.filter(FeeStructure.grade_id == grade_id)
    return query.all()

def create_fee_structure(db: Session, struct_in: FeeStructureCreate, organization_id: UUID, user_id: UUID):
    fs = FeeStructure(**struct_in.model_dump(), organization_id=organization_id)
    db.add(fs)
    db.commit()
    db.refresh(fs)
    log_action(db, organization_id, user_id, "CREATE", "FEE_STRUCTURE", fs.id, new_values=str(struct_in.model_dump()))
    return fs

# Invoice
def get_invoices(db: Session, organization_id: UUID, student_id: Optional[UUID] = None):
    query = db.query(Invoice).filter(Invoice.organization_id == organization_id)
    if student_id:
        query = query.filter(Invoice.student_id == student_id)
    return query.all()

def create_invoice(db: Session, invoice_in: InvoiceCreate, organization_id: UUID, user_id: UUID):
    inv = Invoice(**invoice_in.model_dump(), organization_id=organization_id)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log_action(db, organization_id, user_id, "CREATE", "INVOICE", inv.id, new_values=str(invoice_in.model_dump()))
    return inv

# Payment
def get_payments(db: Session, organization_id: UUID, invoice_id: Optional[UUID] = None):
    query = db.query(Payment).filter(Payment.organization_id == organization_id)
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    return query.all()

def create_payment(db: Session, payment_in: PaymentCreate, organization_id: UUID, user_id: UUID):
    pay = Payment(**payment_in.model_dump(), organization_id=organization_id)
    db.add(pay)
    db.commit()
    db.refresh(pay)
    log_action(db, organization_id, user_id, "CREATE", "PAYMENT", pay.id, new_values=str(payment_in.model_dump()))
    return pay
