from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AcademicYearBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class AcademicYearCreate(AcademicYearBase):
    pass

class AcademicYear(AcademicYearBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
