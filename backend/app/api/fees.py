from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.fee_service import (
    get_fee_types, create_fee_type,
    get_fee_structures, create_fee_structure,
    get_invoices, create_invoice,
    get_payments, create_payment
)
from app.schemas.fee import (
    FeeType,
    FeeTypeCreate,
    FeeStructure,
    FeeStructureCreate,
    Invoice,
    InvoiceCreate,
    Payment,
    PaymentCreate,
)
from app.models.base import Organization, User

router = APIRouter()

# Fee Types
@router.get("/types", response_model=List[FeeType])
def read_fee_types(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_fee_types(db, current_org.id)

@router.post("/types", response_model=FeeType)
def create_fee_type_endpoint(type_in: FeeTypeCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_fee_type(db, type_in, current_org.id, current_user.id)

# Fee Structures
@router.get("/structures", response_model=List[FeeStructure])
def read_structures(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), grade_id: Optional[UUID] = None):
    return get_fee_structures(db, current_org.id, grade_id)

@router.post("/structures", response_model=FeeStructure)
def create_structure_endpoint(struct_in: FeeStructureCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_fee_structure(db, struct_in, current_org.id, current_user.id)

# Invoices
@router.get("/invoices", response_model=List[Invoice])
def read_invoices(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), student_id: Optional[UUID] = None):
    return get_invoices(db, current_org.id, student_id)

@router.post("/invoices", response_model=Invoice)
def create_invoice_endpoint(invoice_in: InvoiceCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_invoice(db, invoice_in, current_org.id, current_user.id)

# Payments
@router.get("/payments", response_model=List[Payment])
def read_payments(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), invoice_id: Optional[UUID] = None):
    return get_payments(db, current_org.id, invoice_id)

@router.post("/payments", response_model=Payment)
def create_payment_endpoint(payment_in: PaymentCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_payment(db, payment_in, current_org.id, current_user.id)
