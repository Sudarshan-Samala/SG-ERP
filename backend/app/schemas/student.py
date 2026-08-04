from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class StudentBase(BaseModel):
    branch_id: UUID
    academic_year_id: UUID
    admission_number: str
    student_name: str
    date_of_birth: datetime
    gender: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
