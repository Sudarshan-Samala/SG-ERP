from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class AdmissionEnquiryBase(BaseModel):
    branch_id: UUID
    academic_year_id: UUID
    student_name: str
    parent_name: str
    email: EmailStr
    phone: str
    lead_source: Optional[str] = None

class AdmissionEnquiryCreate(AdmissionEnquiryBase):
    pass

class AdmissionEnquiry(AdmissionEnquiryBase):
    id: UUID
    organization_id: UUID
    status: str

    class Config:
        from_attributes = True
