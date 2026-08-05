from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from typing import List,Optional
from uuid import UUID
from pydantic import BaseModel,Field
from app.core.database import get_db
from app.api.deps import accessible_branch_ids,enforce_branch_access,get_current_organization,require_permission
from app.services.exam_service import get_exam_types,create_exam_type,get_exams,create_exam,delete_exam,get_exam_schedules,create_exam_schedule,get_exam_results,create_exam_result
from app.schemas.exam import ExamType,ExamTypeCreate,Exam,ExamCreate,ExamSchedule,ExamScheduleCreate,ExamResult,ExamResultCreate
from app.models.base import Organization,Student,User
router=APIRouter()
class BulkResultRequest(BaseModel):results:list[ExamResultCreate]=Field(min_length=1,max_length=200)
@router.get('/types',response_model=List[ExamType])
def read_exam_types(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('exam.read'))):return get_exam_types(db,current_org.id)
@router.post('/types',response_model=ExamType)
def create_exam_type_endpoint(type_in:ExamTypeCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.manage'))):return create_exam_type(db,type_in,current_org.id,current_user.id)
@router.get('/',response_model=List[Exam])
def read_exams(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),skip:int=0,limit:int=100,_:User=Depends(require_permission('exam.read'))):return get_exams(db,current_org.id,skip,limit)
@router.post('/',response_model=Exam)
def create_exam_endpoint(exam_in:ExamCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.manage'))):return create_exam(db,exam_in,current_org.id,current_user.id)
@router.delete('/{exam_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_endpoint(exam_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.manage'))):
    if not delete_exam(db,exam_id,current_org.id,current_user.id):raise HTTPException(status_code=404,detail='Exam not found')
@router.get('/schedules',response_model=List[ExamSchedule])
def read_schedules(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),exam_id:Optional[UUID]=None,_:User=Depends(require_permission('exam.read'))):return get_exam_schedules(db,current_org.id,exam_id)
@router.post('/schedules',response_model=ExamSchedule)
def create_schedule_endpoint(schedule_in:ExamScheduleCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.schedule.manage'))):return create_exam_schedule(db,schedule_in,current_org.id,current_user.id)
@router.get('/results',response_model=List[ExamResult])
def read_results(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),exam_id:Optional[UUID]=None,student_id:Optional[UUID]=None,current_user:User=Depends(require_permission('exam.result.read'))):return get_exam_results(db,current_org.id,exam_id,student_id,None if current_user.is_superuser else accessible_branch_ids(current_user))
@router.get('/results/summary')
def result_summary(exam_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.result.read'))):
    rows=get_exam_results(db,current_org.id,exam_id,None,None if current_user.is_superuser else accessible_branch_ids(current_user));marks=[float(r.marks_obtained) for r in rows]
    return {'exam_id':exam_id,'results':len(rows),'students':len({r.student_id for r in rows}),'average_marks':round(sum(marks)/len(marks),2) if marks else 0,'highest_marks':max(marks) if marks else 0,'lowest_marks':min(marks) if marks else 0}
@router.post('/results/bulk')
def bulk_results(payload:BulkResultRequest,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.result.create'))):
    seen=set();created=[]
    for result in payload.results:
        key=(result.exam_id,result.student_id,result.subject_id)
        if key in seen:raise HTTPException(status_code=400,detail='Duplicate result in bulk request')
        seen.add(key);student=db.query(Student).filter(Student.id==result.student_id,Student.organization_id==current_org.id).first()
        if not student:raise HTTPException(status_code=400,detail='Student does not belong to this organization')
        enforce_branch_access(current_user,student.branch_id);created.append(create_exam_result(db,result,current_org.id,current_user.id))
    return {'created':len(created)}
@router.post('/results',response_model=ExamResult)
def create_result_endpoint(result_in:ExamResultCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('exam.result.create'))):
    student=db.query(Student).filter(Student.id==result_in.student_id,Student.organization_id==current_org.id).first()
    if not student:raise HTTPException(status_code=400,detail='Student does not belong to this organization')
    enforce_branch_access(current_user,student.branch_id);return create_exam_result(db,result_in,current_org.id,current_user.id)
