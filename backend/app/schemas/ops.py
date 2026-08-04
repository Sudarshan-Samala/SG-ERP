from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class NetworkConnectionBase(BaseModel):
    isp_name: str
    plan_details: Optional[str] = None
    bandwidth: Optional[str] = None
    expiry_date: datetime

class NetworkConnection(NetworkConnectionBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class FacilityBase(BaseModel):
    name: str
    type: str

class Facility(FacilityBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class MaintenanceRequestBase(BaseModel):
    facility_id: UUID
    description: str

class MaintenanceRequest(MaintenanceRequestBase):
    id: UUID
    organization_id: UUID
    status: str

    class Config:
        from_attributes = True

class VisitorBase(BaseModel):
    name: str
    purpose: str
    check_in: datetime

class Visitor(VisitorBase):
    id: UUID
    organization_id: UUID
    check_out: Optional[datetime] = None

    class Config:
        from_attributes = True
