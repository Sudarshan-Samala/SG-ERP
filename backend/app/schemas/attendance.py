from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AttendanceBase(BaseModel):
    branch_id: UUID
    student_id: UUID
    date: datetime
    status: str

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
