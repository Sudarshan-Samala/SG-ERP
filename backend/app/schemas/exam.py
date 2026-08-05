from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ExamTypeBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)

class ExamTypeCreate(ExamTypeBase):
    pass

class ExamType(ExamTypeBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class ExamBase(BaseModel):
    exam_type_id: UUID
    name: str = Field(min_length=2, max_length=150)
    start_date: datetime
    end_date: datetime

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self

class ExamCreate(ExamBase):
    pass

class Exam(ExamBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class ExamScheduleBase(BaseModel):
    exam_id: UUID
    subject_id: UUID
    grade_id: UUID
    date: datetime
    max_marks: int = Field(gt=0, le=10000)

class ExamScheduleCreate(ExamScheduleBase):
    pass

class ExamSchedule(ExamScheduleBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class ExamResultBase(BaseModel):
    exam_id: UUID
    student_id: UUID
    subject_id: UUID
    marks_obtained: int = Field(ge=0, le=10000)

class ExamResultCreate(ExamResultBase):
    pass

class ExamResult(ExamResultBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
