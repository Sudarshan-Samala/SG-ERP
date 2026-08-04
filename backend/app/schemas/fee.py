from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class FeeTypeBase(BaseModel):
    name: str

class FeeTypeCreate(FeeTypeBase):
    pass

class FeeType(FeeTypeBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class FeeStructureBase(BaseModel):
    grade_id: UUID
    fee_type_id: UUID
    amount: int

class FeeStructureCreate(FeeStructureBase):
    pass

class FeeStructure(FeeStructureBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    student_id: UUID
    amount_due: int
    due_date: datetime
    status: str

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    invoice_id: UUID
    amount_paid: int
    payment_date: datetime
    payment_method: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
