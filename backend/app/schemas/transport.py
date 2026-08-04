from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class VehicleBase(BaseModel):
    number: str
    capacity: int

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    name: str
    vehicle_id: Optional[UUID] = None

class RouteCreate(RouteBase):
    pass

class Route(RouteBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class DriverBase(BaseModel):
    name: str
    license_number: str

class DriverCreate(DriverBase):
    pass

class Driver(DriverBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
