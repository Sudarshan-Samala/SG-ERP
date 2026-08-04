from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.ops_service import create_network, create_facility, create_maintenance, create_visitor
from app.schemas.ops import NetworkConnection, Facility, MaintenanceRequest, Visitor
from app.models.base import Organization

router = APIRouter()

@router.post("/network", response_model=NetworkConnection)
def create_network_endpoint(net_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_network(db, net_in, current_org.id)

@router.post("/facilities", response_model=Facility)
def create_facility_endpoint(fac_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_facility(db, fac_in, current_org.id)

@router.post("/maintenance", response_model=MaintenanceRequest)
def create_maintenance_endpoint(maint_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_maintenance(db, maint_in, current_org.id)

@router.post("/visitors", response_model=Visitor)
def create_visitor_endpoint(vis_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_visitor(db, vis_in, current_org.id)
