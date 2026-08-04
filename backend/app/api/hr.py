from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.hr_service import (
    get_employees, create_employee,
    get_salary_structures, create_salary_structure,
    get_payrolls, create_payroll
)
from app.schemas.hr import (
    Employee,
    EmployeeCreate,
    SalaryStructure,
    SalaryStructureCreate,
    Payroll,
    PayrollCreate,
)
from app.models.base import Organization, User

router = APIRouter()

# Employees
@router.get("/employees", response_model=List[Employee])
def read_employees(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), department: Optional[str] = None):
    return get_employees(db, current_org.id, department)

@router.post("/employees", response_model=Employee)
def create_employee_endpoint(emp_in: EmployeeCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_employee(db, emp_in, current_org.id, current_user.id)

# Salary Structures
@router.get("/salary-structures", response_model=List[SalaryStructure])
def read_salary_structures(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), employee_id: Optional[UUID] = None):
    return get_salary_structures(db, current_org.id, employee_id)

@router.post("/salary-structures", response_model=SalaryStructure)
def create_salary_structure_endpoint(struct_in: SalaryStructureCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_salary_structure(db, struct_in, current_org.id, current_user.id)

# Payroll
@router.get("/payroll", response_model=List[Payroll])
def read_payrolls(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), employee_id: Optional[UUID] = None):
    return get_payrolls(db, current_org.id, employee_id)

@router.post("/payroll", response_model=Payroll)
def create_payroll_endpoint(payroll_in: PayrollCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_payroll(db, payroll_in, current_org.id, current_user.id)
