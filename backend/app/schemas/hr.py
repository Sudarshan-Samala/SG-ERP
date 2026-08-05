from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class EmployeeBase(BaseModel):
    user_id: UUID
    employee_id: str = Field(min_length=1, max_length=50)
    department: str = Field(min_length=2, max_length=100)
    designation: str = Field(min_length=2, max_length=100)

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class SalaryStructureBase(BaseModel):
    employee_id: UUID
    basic_salary: int = Field(ge=0)
    hra: int = Field(ge=0)

class SalaryStructureCreate(SalaryStructureBase):
    pass

class SalaryStructure(SalaryStructureBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class PayrollBase(BaseModel):
    employee_id: UUID
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2200)
    net_salary: int = Field(ge=0)

class PayrollCreate(PayrollBase):
    pass

class Payroll(PayrollBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
