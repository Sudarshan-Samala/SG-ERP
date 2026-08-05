from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import Employee, Payroll, SalaryStructure, User
from app.schemas.hr import EmployeeCreate, PayrollCreate, SalaryStructureCreate
from app.services.audit.audit_service import log_action


def _require_employee(db: Session, employee_id: UUID, organization_id: UUID):
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.organization_id == organization_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee does not belong to this organization")
    return employee


def get_employees(db: Session, organization_id: UUID, department: Optional[str] = None):
    query = db.query(Employee).filter(Employee.organization_id == organization_id)
    if department: query = query.filter(Employee.department == department)
    return query.all()


def create_employee(db: Session, emp_in: EmployeeCreate, organization_id: UUID, user_id: UUID):
    user = db.query(User).filter(User.id == emp_in.user_id, User.organization_id == organization_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not belong to this organization")
    existing = db.query(Employee).filter(Employee.organization_id == organization_id, Employee.user_id == emp_in.user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee already exists for this user")
    emp = Employee(**emp_in.model_dump(), organization_id=organization_id)
    db.add(emp); db.commit(); db.refresh(emp)
    log_action(db, organization_id, user_id, "CREATE", "EMPLOYEE", emp.id, new_values=str(emp_in.model_dump()))
    return emp


def get_salary_structures(db: Session, organization_id: UUID, employee_id: Optional[UUID] = None):
    query = db.query(SalaryStructure).filter(SalaryStructure.organization_id == organization_id)
    if employee_id: query = query.filter(SalaryStructure.employee_id == employee_id)
    return query.all()


def create_salary_structure(db: Session, struct_in: SalaryStructureCreate, organization_id: UUID, user_id: UUID):
    _require_employee(db, struct_in.employee_id, organization_id)
    ss = SalaryStructure(**struct_in.model_dump(), organization_id=organization_id)
    db.add(ss); db.commit(); db.refresh(ss)
    log_action(db, organization_id, user_id, "CREATE", "SALARY_STRUCTURE", ss.id, new_values=str(struct_in.model_dump()))
    return ss


def get_payrolls(db: Session, organization_id: UUID, employee_id: Optional[UUID] = None):
    query = db.query(Payroll).filter(Payroll.organization_id == organization_id)
    if employee_id: query = query.filter(Payroll.employee_id == employee_id)
    return query.all()


def create_payroll(db: Session, payroll_in: PayrollCreate, organization_id: UUID, user_id: UUID):
    _require_employee(db, payroll_in.employee_id, organization_id)
    existing = db.query(Payroll).filter(Payroll.organization_id == organization_id, Payroll.employee_id == payroll_in.employee_id, Payroll.month == payroll_in.month, Payroll.year == payroll_in.year).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payroll already exists for this employee and period")
    py = Payroll(**payroll_in.model_dump(), organization_id=organization_id)
    db.add(py); db.commit(); db.refresh(py)
    log_action(db, organization_id, user_id, "CREATE", "PAYROLL", py.id, new_values=str(payroll_in.model_dump()))
    return py
