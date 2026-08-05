from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.signup import router as signup_router
from app.api.organizations import router as org_router
from app.api.branches import router as branch_router
from app.api.rbac import router as rbac_router
from app.api.academic import router as academic_router
from app.api.users import router as user_router
from app.api.admissions import router as admission_router
from app.api.students import router as student_router
from app.api.academic_management import router as academic_management_router
from app.api.attendance import router as attendance_router
from app.api.exams import router as exam_router
from app.api.fees import router as fee_router
from app.api.finance import router as finance_router
from app.api.hr import router as hr_router
from app.api.transport import router as transport_router
from app.api.inventory_assets import router as inv_asset_router
from app.api.helpdesk import router as helpdesk_router
from app.api.ops import router as ops_router
from app.api.events import router as event_router
from app.api.communication import router as comm_router
from app.api.circular import router as circular_router
from app.api.document import router as doc_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notification_router
from app.api.reports import router as report_router
app=FastAPI(title=settings.PROJECT_NAME,openapi_url='/api/v1/openapi.json')
app.add_middleware(CORSMiddleware,allow_origins=settings.TRUSTED_ORIGINS,allow_credentials=True,allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],allow_headers=['Authorization','Content-Type','X-CSRF-Token'])
app.include_router(auth_router,prefix='/api/v1/auth',tags=['auth']);app.include_router(signup_router,prefix='/api/v1/auth',tags=['auth']);app.include_router(org_router,prefix='/api/v1/organizations',tags=['organizations']);app.include_router(branch_router,prefix='/api/v1/branches',tags=['branches']);app.include_router(rbac_router,prefix='/api/v1/rbac',tags=['rbac']);app.include_router(academic_router,prefix='/api/v1/academic',tags=['academic']);app.include_router(user_router,prefix='/api/v1/users',tags=['users']);app.include_router(admission_router,prefix='/api/v1/admissions',tags=['admissions']);app.include_router(student_router,prefix='/api/v1/students',tags=['students']);app.include_router(academic_management_router,prefix='/api/v1/academic-mgmt',tags=['academic-mgmt']);app.include_router(attendance_router,prefix='/api/v1/attendance',tags=['attendance']);app.include_router(exam_router,prefix='/api/v1/exams',tags=['exams']);app.include_router(fee_router,prefix='/api/v1/fees',tags=['fees']);app.include_router(finance_router,prefix='/api/v1/finance',tags=['finance']);app.include_router(hr_router,prefix='/api/v1/hr',tags=['hr']);app.include_router(transport_router,prefix='/api/v1/transport',tags=['transport']);app.include_router(inv_asset_router,prefix='/api/v1/inventory-assets',tags=['inventory-assets']);app.include_router(helpdesk_router,prefix='/api/v1/helpdesk',tags=['helpdesk']);app.include_router(ops_router,prefix='/api/v1/ops',tags=['ops']);app.include_router(event_router,prefix='/api/v1/events',tags=['events']);app.include_router(comm_router,prefix='/api/v1/communication',tags=['communication']);app.include_router(circular_router,prefix='/api/v1/circulars',tags=['circulars']);app.include_router(doc_router,prefix='/api/v1/documents',tags=['documents']);app.include_router(dashboard_router,prefix='/api/v1/dashboard',tags=['dashboard']);app.include_router(notification_router,prefix='/api/v1/notifications',tags=['notifications']);app.include_router(report_router,prefix='/api/v1/reports',tags=['reports'])
@app.get('/')
def read_root():return {'message':'Welcome to Sampurna Gnana ERP API'}
@app.get('/health')
def health_check():return {'status':'healthy'}
