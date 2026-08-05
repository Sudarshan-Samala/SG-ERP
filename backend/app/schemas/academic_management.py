from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NormalizedNameMixin(BaseModel):
    @field_validator("name", check_fields=False)
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value

class GradeBase(NormalizedNameMixin):
    branch_id: UUID
    name: str = Field(min_length=1, max_length=100)

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class SectionBase(NormalizedNameMixin):
    branch_id: UUID
    grade_id: UUID
    name: str = Field(min_length=1, max_length=50)

class SectionCreate(SectionBase):
    pass

class Section(SectionBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class SubjectBase(NormalizedNameMixin):
    name: str = Field(min_length=1, max_length=150)
    code: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
