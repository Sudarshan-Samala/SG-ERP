from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class AdmissionEnquiryBase(BaseModel):
    branch_id: UUID
    academic_year_id: UUID
    student_name: str = Field(min_length=2, max_length=150)
    parent_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    lead_source: Optional[str] = Field(default=None, max_length=100)

    @field_validator("student_name", "parent_name", "phone")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("lead_source")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class AdmissionEnquiryCreate(AdmissionEnquiryBase):
    pass


class AdmissionEnquiry(AdmissionEnquiryBase):
    id: UUID
    organization_id: UUID
    status: str

    class Config:
        from_attributes = True
