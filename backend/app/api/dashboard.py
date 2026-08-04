from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.base import Student, Employee, Invoice, Ticket, User

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org_id = current_user.organization_id
    
    students_count = db.query(Student).filter(Student.organization_id == org_id).count()
    employees_count = db.query(Employee).filter(Employee.organization_id == org_id).count()
    
    return {
        "students": students_count,
        "employees": employees_count,
        "open_tickets": db.query(Ticket).filter(Ticket.organization_id == org_id, Ticket.status == "OPEN").count()
    }
