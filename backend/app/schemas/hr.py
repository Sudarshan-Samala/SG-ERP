from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class EmployeeBase(BaseModel):
    user_id: UUID
    employee_id: str
    department: str
    designation: str

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class SalaryStructureBase(BaseModel):
    employee_id: UUID
    basic_salary: int
    hra: int

class SalaryStructureCreate(SalaryStructureBase):
    pass

class SalaryStructure(SalaryStructureBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class PayrollBase(BaseModel):
    employee_id: UUID
    month: int
    year: int
    net_salary: int

class PayrollCreate(PayrollBase):
    pass

class Payroll(PayrollBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
