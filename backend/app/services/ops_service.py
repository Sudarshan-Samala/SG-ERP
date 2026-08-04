from sqlalchemy.orm import Session
from app.models.base import NetworkConnection, Facility, MaintenanceRequest, Visitor
from uuid import UUID

def create_network(db: Session, net_in, organization_id: UUID):
    net = NetworkConnection(**net_in.dict(), organization_id=organization_id)
    db.add(net)
    db.commit()
    db.refresh(net)
    return net

def create_facility(db: Session, fac_in, organization_id: UUID):
    fac = Facility(**fac_in.dict(), organization_id=organization_id)
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

def create_maintenance(db: Session, maint_in, organization_id: UUID):
    maint = MaintenanceRequest(**maint_in.dict(), organization_id=organization_id, status="OPEN")
    db.add(maint)
    db.commit()
    db.refresh(maint)
    return maint

def create_visitor(db: Session, vis_in, organization_id: UUID):
    vis = Visitor(**vis_in.dict(), organization_id=organization_id)
    db.add(vis)
    db.commit()
    db.refresh(vis)
    return vis
