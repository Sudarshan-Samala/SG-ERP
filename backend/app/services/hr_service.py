from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import Employee, Payroll, SalaryStructure, User
from app.services.audit.audit_service import log_action

def _require_employee(db:Session,employee_id:UUID,organization_id:UUID):
    employee=db.query(Employee).filter(Employee.id==employee_id,Employee.organization_id==organization_id).first()
    if not employee:raise HTTPException(status_code=400,detail='Employee does not belong to this organization')
    return employee
def get_employees(db,organization_id,department=None):
    q=db.query(Employee).filter(Employee.organization_id==organization_id)
    if department:q=q.filter(Employee.department==department)
    return q.order_by(Employee.employee_id).all()
def create_employee(db,emp_in,organization_id,user_id):
    user=db.query(User).filter(User.id==emp_in.user_id,User.organization_id==organization_id,User.is_active.is_(True)).first()
    if not user:raise HTTPException(status_code=400,detail='Active user does not belong to this organization')
    employee_code=emp_in.employee_id.strip().upper();department=emp_in.department.strip();designation=emp_in.designation.strip()
    duplicate=db.query(Employee).filter(Employee.organization_id==organization_id,((Employee.user_id==emp_in.user_id)|(func.lower(Employee.employee_id)==employee_code.lower()))).first()
    if duplicate:raise HTTPException(status_code=409,detail='Employee user or employee ID already exists')
    emp=Employee(user_id=emp_in.user_id,employee_id=employee_code,department=department,designation=designation,organization_id=organization_id);db.add(emp)
    try:db.commit();db.refresh(emp)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Employee user or employee ID already exists') from exc
    log_action(db,organization_id,user_id,'CREATE','EMPLOYEE',emp.id,new_values=str(emp_in.model_dump()));return emp
def get_salary_structures(db,organization_id,employee_id=None):
    q=db.query(SalaryStructure).filter(SalaryStructure.organization_id==organization_id)
    if employee_id:q=q.filter(SalaryStructure.employee_id==employee_id)
    return q.order_by(SalaryStructure.employee_id).all()
def create_salary_structure(db,struct_in,organization_id,user_id):
    _require_employee(db,struct_in.employee_id,organization_id)
    if struct_in.basic_salary+struct_in.hra<=0:raise HTTPException(status_code=422,detail='Gross salary must be greater than zero')
    if db.query(SalaryStructure).filter(SalaryStructure.organization_id==organization_id,SalaryStructure.employee_id==struct_in.employee_id).first():raise HTTPException(status_code=409,detail='Salary structure already exists for this employee')
    ss=SalaryStructure(**struct_in.model_dump(),organization_id=organization_id);db.add(ss)
    try:db.commit();db.refresh(ss)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Salary structure already exists for this employee') from exc
    log_action(db,organization_id,user_id,'CREATE','SALARY_STRUCTURE',ss.id,new_values=str(struct_in.model_dump()));return ss
def get_payrolls(db,organization_id,employee_id=None):
    q=db.query(Payroll).filter(Payroll.organization_id==organization_id)
    if employee_id:q=q.filter(Payroll.employee_id==employee_id)
    return q.order_by(Payroll.year.desc(),Payroll.month.desc()).all()
def create_payroll(db,payroll_in,organization_id,user_id):
    _require_employee(db,payroll_in.employee_id,organization_id);salary=db.query(SalaryStructure).filter(SalaryStructure.organization_id==organization_id,SalaryStructure.employee_id==payroll_in.employee_id).first()
    if not salary:raise HTTPException(status_code=409,detail='Create a salary structure before payroll')
    if payroll_in.net_salary<=0:raise HTTPException(status_code=422,detail='Net salary must be greater than zero')
    if payroll_in.net_salary>salary.basic_salary+salary.hra:raise HTTPException(status_code=400,detail='Net salary cannot exceed configured gross salary')
    if db.query(Payroll).filter(Payroll.organization_id==organization_id,Payroll.employee_id==payroll_in.employee_id,Payroll.month==payroll_in.month,Payroll.year==payroll_in.year).first():raise HTTPException(status_code=409,detail='Payroll already exists for this employee and period')
    py=Payroll(**payroll_in.model_dump(),organization_id=organization_id);db.add(py)
    try:db.commit();db.refresh(py)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Payroll already exists for this employee and period') from exc
    log_action(db,organization_id,user_id,'CREATE','PAYROLL',py.id,new_values=str(payroll_in.model_dump()));return py
