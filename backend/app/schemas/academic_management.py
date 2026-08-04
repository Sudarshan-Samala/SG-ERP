from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class GradeBase(BaseModel):
    branch_id: UUID
    name: str

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    branch_id: UUID
    grade_id: UUID
    name: str

class SectionCreate(SectionBase):
    pass

class Section(SectionBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class SubjectBase(BaseModel):
    name: str
    code: str

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
