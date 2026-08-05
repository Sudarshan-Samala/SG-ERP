from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class StudentBase(BaseModel):
    branch_id: UUID
    academic_year_id: UUID
    admission_number: str = Field(min_length=1, max_length=50)
    student_name: str = Field(min_length=2, max_length=150)
    date_of_birth: datetime
    gender: Literal["male", "female", "other"]
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=7, max_length=20)

    @field_validator("admission_number", "student_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def reject_future_birth_date(cls, value: datetime) -> datetime:
        if value > datetime.now(value.tzinfo):
            raise ValueError("date_of_birth cannot be in the future")
        return value


class StudentCreate(StudentBase):
    pass


class Student(StudentBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
