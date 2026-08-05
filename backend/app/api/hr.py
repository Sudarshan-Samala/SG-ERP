import csv
import io
from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.hr_service import get_employees, create_employee, get_salary_structures, create_salary_structure, get_payrolls, create_payroll
from app.schemas.hr import Employee, EmployeeCreate, SalaryStructure, SalaryStructureCreate, Payroll, PayrollCreate
from app.models.base import Employee as EmployeeModel, Organization, Payroll as PayrollModel, User
router=APIRouter()
@router.get('/employees',response_model=List[Employee])
def read_employees(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),department:Optional[str]=None,_:User=Depends(require_permission('hr.employee.read'))):return get_employees(db,current_org.id,department)
@router.post('/employees',response_model=Employee)
def create_employee_endpoint(emp_in:EmployeeCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('hr.employee.create'))):return create_employee(db,emp_in,current_org.id,current_user.id)
@router.get('/salary-structures',response_model=List[SalaryStructure])
def read_salary_structures(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),employee_id:Optional[UUID]=None,_:User=Depends(require_permission('hr.salary.read'))):return get_salary_structures(db,current_org.id,employee_id)
@router.post('/salary-structures',response_model=SalaryStructure)
def create_salary_structure_endpoint(struct_in:SalaryStructureCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('hr.salary.manage'))):return create_salary_structure(db,struct_in,current_org.id,current_user.id)
@router.get('/payroll',response_model=List[Payroll])
def read_payrolls(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),employee_id:Optional[UUID]=None,_:User=Depends(require_permission('hr.payroll.read'))):return get_payrolls(db,current_org.id,employee_id)
@router.post('/payroll',response_model=Payroll)
def create_payroll_endpoint(payroll_in:PayrollCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('hr.payroll.create'))):return create_payroll(db,payroll_in,current_org.id,current_user.id)

def _period_query(db,org_id,month,year):
    q=db.query(PayrollModel).filter(PayrollModel.organization_id==org_id)
    if month:q=q.filter(PayrollModel.month==month)
    if year:q=q.filter(PayrollModel.year==year)
    return q
@router.get('/payroll-summary')
def payroll_summary(month:Optional[int]=None,year:Optional[int]=None,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('hr.payroll.read'))):
    q=_period_query(db,current_org.id,month,year);return {'month':month,'year':year,'payroll_count':q.count(),'total_net_salary':int(q.with_entities(func.coalesce(func.sum(PayrollModel.net_salary),0)).scalar() or 0),'employee_count':q.with_entities(PayrollModel.employee_id).distinct().count()}
@router.get('/payroll-export.csv')
def payroll_export(month:Optional[int]=None,year:Optional[int]=None,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('hr.payroll.read'))):
    rows=_period_query(db,current_org.id,month,year).join(EmployeeModel,EmployeeModel.id==PayrollModel.employee_id).with_entities(EmployeeModel.employee_id,EmployeeModel.department,EmployeeModel.designation,PayrollModel.month,PayrollModel.year,PayrollModel.net_salary).order_by(PayrollModel.year.desc(),PayrollModel.month.desc(),EmployeeModel.employee_id).all();out=io.StringIO();writer=csv.writer(out);writer.writerow(['employee_id','department','designation','month','year','net_salary']);writer.writerows(rows);return Response(content=out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="payroll.csv"'})
