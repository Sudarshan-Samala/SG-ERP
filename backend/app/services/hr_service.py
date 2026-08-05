from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Employee, Payroll, SalaryStructure, User
from app.schemas.hr import EmployeeCreate, PayrollCreate, SalaryStructureCreate
from app.services.audit.audit_service import log_action


def _require_employee(db: Session, employee_id: UUID, organization_id: UUID):
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.organization_id == organization_id).first()
    if not employee: raise HTTPException(status_code=400, detail="Employee does not belong to this organization")
    return employee


def get_employees(db, organization_id, department=None):
    query = db.query(Employee).filter(Employee.organization_id == organization_id)
    if department: query = query.filter(Employee.department == department)
    return query.order_by(Employee.employee_id).all()


def create_employee(db, emp_in, organization_id, user_id):
    user = db.query(User).filter(User.id == emp_in.user_id, User.organization_id == organization_id).first()
    if not user: raise HTTPException(status_code=400, detail="User does not belong to this organization")
    duplicate = db.query(Employee).filter(Employee.organization_id == organization_id, ((Employee.user_id == emp_in.user_id) | (Employee.employee_id == emp_in.employee_id))).first()
    if duplicate: raise HTTPException(status_code=409, detail="Employee user or employee ID already exists")
    emp = Employee(**emp_in.model_dump(), organization_id=organization_id); db.add(emp)
    try: db.commit(); db.refresh(emp)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Employee user or employee ID already exists") from exc
    log_action(db, organization_id, user_id, "CREATE", "EMPLOYEE", emp.id, new_values=str(emp_in.model_dump())); return emp


def get_salary_structures(db, organization_id, employee_id=None):
    query = db.query(SalaryStructure).filter(SalaryStructure.organization_id == organization_id)
    if employee_id: query = query.filter(SalaryStructure.employee_id == employee_id)
    return query.all()


def create_salary_structure(db, struct_in, organization_id, user_id):
    _require_employee(db, struct_in.employee_id, organization_id)
    if getattr(struct_in, "basic_salary", 0) < 0: raise HTTPException(status_code=400, detail="Basic salary cannot be negative")
    ss = SalaryStructure(**struct_in.model_dump(), organization_id=organization_id); db.add(ss); db.commit(); db.refresh(ss)
    log_action(db, organization_id, user_id, "CREATE", "SALARY_STRUCTURE", ss.id, new_values=str(struct_in.model_dump())); return ss


def get_payrolls(db, organization_id, employee_id=None):
    query = db.query(Payroll).filter(Payroll.organization_id == organization_id)
    if employee_id: query = query.filter(Payroll.employee_id == employee_id)
    return query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()


def create_payroll(db, payroll_in, organization_id, user_id):
    _require_employee(db, payroll_in.employee_id, organization_id)
    if not 1 <= payroll_in.month <= 12: raise HTTPException(status_code=400, detail="Payroll month must be between 1 and 12")
    if payroll_in.year < 2000 or payroll_in.year > 2100: raise HTTPException(status_code=400, detail="Payroll year is invalid")
    existing = db.query(Payroll).filter(Payroll.organization_id == organization_id, Payroll.employee_id == payroll_in.employee_id, Payroll.month == payroll_in.month, Payroll.year == payroll_in.year).first()
    if existing: raise HTTPException(status_code=409, detail="Payroll already exists for this employee and period")
    py = Payroll(**payroll_in.model_dump(), organization_id=organization_id); db.add(py)
    try: db.commit(); db.refresh(py)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Payroll already exists for this employee and period") from exc
    log_action(db, organization_id, user_id, "CREATE", "PAYROLL", py.id, new_values=str(payroll_in.model_dump())); return py
