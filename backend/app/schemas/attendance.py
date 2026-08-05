from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator


class AttendanceBase(BaseModel):
    branch_id: UUID
    student_id: UUID
    date: datetime
    status: Literal["present", "absent", "late", "excused"]

    @field_validator("date")
    @classmethod
    def reject_future_attendance(cls, value: datetime) -> datetime:
        if value > datetime.now(value.tzinfo):
            raise ValueError("attendance date cannot be in the future")
        return value


class AttendanceCreate(AttendanceBase):
    pass


class Attendance(AttendanceBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
