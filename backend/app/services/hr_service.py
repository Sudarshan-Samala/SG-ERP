from sqlalchemy.orm import Session
from app.models.base import Employee, SalaryStructure, Payroll
from app.schemas.hr import EmployeeCreate, SalaryStructureCreate, PayrollCreate
from app.services.audit.audit_service import log_action
from uuid import UUID
from typing import Optional

# Employee
def get_employees(db: Session, organization_id: UUID, department: Optional[str] = None):
    query = db.query(Employee).filter(Employee.organization_id == organization_id)
    if department:
        query = query.filter(Employee.department == department)
    return query.all()

def create_employee(db: Session, emp_in: EmployeeCreate, organization_id: UUID, user_id: UUID):
    emp = Employee(**emp_in.model_dump(), organization_id=organization_id)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    log_action(db, organization_id, user_id, "CREATE", "EMPLOYEE", emp.id, new_values=str(emp_in.model_dump()))
    return emp

# SalaryStructure
def get_salary_structures(db: Session, organization_id: UUID, employee_id: Optional[UUID] = None):
    query = db.query(SalaryStructure).filter(SalaryStructure.organization_id == organization_id)
    if employee_id:
        query = query.filter(SalaryStructure.employee_id == employee_id)
    return query.all()

def create_salary_structure(db: Session, struct_in: SalaryStructureCreate, organization_id: UUID, user_id: UUID):
    ss = SalaryStructure(**struct_in.model_dump(), organization_id=organization_id)
    db.add(ss)
    db.commit()
    db.refresh(ss)
    log_action(db, organization_id, user_id, "CREATE", "SALARY_STRUCTURE", ss.id, new_values=str(struct_in.model_dump()))
    return ss

# Payroll
def get_payrolls(db: Session, organization_id: UUID, employee_id: Optional[UUID] = None):
    query = db.query(Payroll).filter(Payroll.organization_id == organization_id)
    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)
    return query.all()

def create_payroll(db: Session, payroll_in: PayrollCreate, organization_id: UUID, user_id: UUID):
    py = Payroll(**payroll_in.model_dump(), organization_id=organization_id)
    db.add(py)
    db.commit()
    db.refresh(py)
    log_action(db, organization_id, user_id, "CREATE", "PAYROLL", py.id, new_values=str(payroll_in.model_dump()))
    return py
