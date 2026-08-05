from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import accessible_branch_ids, enforce_branch_access, get_current_organization, require_permission
from app.services.attendance_service import get_attendance, create_attendance
from app.schemas.attendance import Attendance, AttendanceCreate
from app.models.base import Organization, Student, User

router = APIRouter()
class BulkAttendanceRequest(BaseModel):
    branch_id: UUID
    date: datetime
    records: list[dict] = Field(min_length=1, max_length=200)

@router.get("/", response_model=List[Attendance])
def read_attendance(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),branch_id:Optional[UUID]=None,student_id:Optional[UUID]=None,date:Optional[datetime]=None,skip:int=0,limit:int=100,current_user:User=Depends(require_permission("attendance.read"))):
    allowed=None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:enforce_branch_access(current_user,branch_id)
    if student_id:
        student=db.query(Student).filter(Student.id==student_id,Student.organization_id==current_org.id).first()
        if student:enforce_branch_access(current_user,student.branch_id)
    rows=get_attendance(db,current_org.id,branch_id,student_id,date,skip,min(max(limit,1),500));return rows if allowed is None else [r for r in rows if r.branch_id in allowed]

@router.get('/exceptions')
def attendance_exceptions(date:datetime,branch_id:Optional[UUID]=None,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('attendance.read'))):
    allowed=None if current_user.is_superuser else accessible_branch_ids(current_user)
    if branch_id:enforce_branch_access(current_user,branch_id)
    students=db.query(Student).filter(Student.organization_id==current_org.id)
    if branch_id:students=students.filter(Student.branch_id==branch_id)
    elif allowed is not None:students=students.filter(Student.branch_id.in_(allowed)) if allowed else students.filter(False)
    student_rows=students.all();marked=get_attendance(db,current_org.id,branch_id,None,date,0,5000);marked_ids={r.student_id for r in marked};missing=[{'student_id':s.id,'student_name':s.student_name,'admission_number':s.admission_number,'branch_id':s.branch_id} for s in student_rows if s.id not in marked_ids]
    return {'date':date.date().isoformat(),'students':len(student_rows),'marked':len(marked_ids),'missing_count':len(missing),'missing':missing}

@router.post('/bulk')
def bulk_attendance(payload:BulkAttendanceRequest,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('attendance.mark'))):
    enforce_branch_access(current_user,payload.branch_id);created=[];seen=set()
    for item in payload.records:
        try:sid=UUID(str(item.get('student_id')));status_value=str(item.get('status','')).upper()
        except Exception:raise HTTPException(status_code=400,detail='Invalid student attendance record')
        if sid in seen:raise HTTPException(status_code=400,detail='Duplicate student in bulk attendance request')
        seen.add(sid)
        if status_value not in {'PRESENT','ABSENT','LATE'}:raise HTTPException(status_code=400,detail='Invalid attendance status')
        created.append(create_attendance(db,AttendanceCreate(branch_id=payload.branch_id,student_id=sid,date=payload.date,status=status_value),current_org.id,current_user.id))
    return {'created':len(created)}

@router.post("/",response_model=Attendance)
def create_attendance_endpoint(att_in:AttendanceCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission("attendance.mark"))):
    student=db.query(Student).filter(Student.id==att_in.student_id,Student.organization_id==current_org.id).first()
    if student:enforce_branch_access(current_user,student.branch_id)
    enforce_branch_access(current_user,att_in.branch_id);return create_attendance(db,att_in,current_org.id,current_user.id)
