from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ExamTypeBase(BaseModel):
    name: str

class ExamTypeCreate(ExamTypeBase):
    pass

class ExamType(ExamTypeBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class ExamBase(BaseModel):
    exam_type_id: UUID
    name: str
    start_date: datetime
    end_date: datetime

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
    max_marks: int

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
    marks_obtained: int

class ExamResultCreate(ExamResultBase):
    pass

class ExamResult(ExamResultBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
