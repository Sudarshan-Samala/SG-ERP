from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.services.fee_service import get_fee_types, create_fee_type, get_fee_structures, create_fee_structure, get_invoices, create_invoice, get_payments, create_payment, get_student_branch_id, get_invoice_branch_id
from app.schemas.fee import FeeType, FeeTypeCreate, FeeStructure, FeeStructureCreate, Invoice, InvoiceCreate, Payment, PaymentCreate
from app.models.base import Invoice as InvoiceModel, Organization, Payment as PaymentModel, Student, User

router=APIRouter()
@router.get('/types',response_model=List[FeeType])
def read_fee_types(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('fees.read'))):return get_fee_types(db,current_org.id)
@router.post('/types',response_model=FeeType)
def create_fee_type_endpoint(type_in:FeeTypeCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.manage'))):return create_fee_type(db,type_in,current_org.id,current_user.id)
@router.get('/structures',response_model=List[FeeStructure])
def read_structures(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),grade_id:Optional[UUID]=None,_:User=Depends(require_permission('fees.read'))):return get_fee_structures(db,current_org.id,grade_id)
@router.post('/structures',response_model=FeeStructure)
def create_structure_endpoint(struct_in:FeeStructureCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.manage'))):return create_fee_structure(db,struct_in,current_org.id,current_user.id)
@router.get('/invoices',response_model=List[Invoice])
def read_invoices(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),student_id:Optional[UUID]=None,current_user:User=Depends(require_permission('fees.read'))):
    branch_ids=None if current_user.is_superuser else accessible_branch_ids(current_user)
    if student_id:enforce_branch_access(current_user,get_student_branch_id(db,student_id,current_org.id))
    return get_invoices(db,current_org.id,student_id,branch_ids)
@router.post('/invoices',response_model=Invoice)
def create_invoice_endpoint(invoice_in:InvoiceCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.invoice.create'))):enforce_branch_access(current_user,get_student_branch_id(db,invoice_in.student_id,current_org.id));return create_invoice(db,invoice_in,current_org.id,current_user.id)
@router.get('/payments',response_model=List[Payment])
def read_payments(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),invoice_id:Optional[UUID]=None,current_user:User=Depends(require_permission('fees.read'))):
    branch_ids=None if current_user.is_superuser else accessible_branch_ids(current_user)
    if invoice_id:enforce_branch_access(current_user,get_invoice_branch_id(db,invoice_id,current_org.id))
    return get_payments(db,current_org.id,invoice_id,branch_ids)
@router.post('/payments',response_model=Payment)
def create_payment_endpoint(payment_in:PaymentCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.payment.collect'))):enforce_branch_access(current_user,get_invoice_branch_id(db,payment_in.invoice_id,current_org.id));return create_payment(db,payment_in,current_org.id,current_user.id)

@router.get('/students/{student_id}/statement')
def student_statement(student_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.read'))):
    enforce_branch_access(current_user,get_student_branch_id(db,student_id,current_org.id));student=db.query(Student).filter(Student.id==student_id,Student.organization_id==current_org.id).first();invoices=get_invoices(db,current_org.id,student_id)
    rows=[];total=paid=0
    for invoice in invoices:
        payments=db.query(PaymentModel).filter(PaymentModel.organization_id==current_org.id,PaymentModel.invoice_id==invoice.id).order_by(PaymentModel.payment_date).all();p=sum(x.amount_paid for x in payments);total+=invoice.amount_due;paid+=p;rows.append({'invoice_id':invoice.id,'due_date':invoice.due_date,'amount_due':invoice.amount_due,'paid':p,'outstanding':invoice.amount_due-p,'status':invoice.status,'payments':[{'id':x.id,'amount_paid':x.amount_paid,'payment_date':x.payment_date,'payment_method':x.payment_method} for x in payments]})
    return {'student':{'id':student.id,'name':student.student_name,'admission_number':student.admission_number},'total_invoiced':total,'total_paid':paid,'outstanding':total-paid,'invoices':rows}

@router.get('/payments/{payment_id}/receipt')
def payment_receipt(payment_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('fees.read'))):
    payment=db.query(PaymentModel).filter(PaymentModel.id==payment_id,PaymentModel.organization_id==current_org.id).first()
    if not payment:raise HTTPException(status_code=404,detail='Payment not found')
    enforce_branch_access(current_user,get_invoice_branch_id(db,payment.invoice_id,current_org.id));invoice=db.query(InvoiceModel).filter(InvoiceModel.id==payment.invoice_id).first();student=db.query(Student).filter(Student.id==invoice.student_id,Student.organization_id==current_org.id).first()
    return {'receipt_number':f'SG-{str(payment.id).split("-")[0].upper()}','payment_id':payment.id,'payment_date':payment.payment_date,'payment_method':payment.payment_method,'amount_paid':payment.amount_paid,'invoice_id':invoice.id,'student_name':student.student_name,'admission_number':student.admission_number}
