from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VehicleBase(BaseModel):
    number: str = Field(min_length=3, max_length=30)
    capacity: int = Field(gt=0, le=200)

    @field_validator("number")
    @classmethod
    def normalize_vehicle_number(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("vehicle number must not be blank")
        return value

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    vehicle_id: Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def normalize_route_name(cls, value: str) -> str:
        return value.strip()

class RouteCreate(RouteBase):
    pass

class Route(RouteBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class DriverBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    license_number: str = Field(min_length=3, max_length=50)

    @field_validator("name", "license_number")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

class DriverCreate(DriverBase):
    pass

class Driver(DriverBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
