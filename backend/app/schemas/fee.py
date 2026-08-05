from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class FeeTypeBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)

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
    amount: int = Field(gt=0)

class FeeStructureCreate(FeeStructureBase):
    pass

class FeeStructure(FeeStructureBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    student_id: UUID
    amount_due: int = Field(gt=0)
    due_date: datetime
    status: Literal["draft", "issued", "partially_paid", "paid", "overdue", "cancelled"] = "draft"

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    invoice_id: UUID
    amount_paid: int = Field(gt=0)
    payment_date: datetime
    payment_method: Literal["cash", "card", "upi", "bank_transfer", "cheque", "online"]

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
