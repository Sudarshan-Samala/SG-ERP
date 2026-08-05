from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.transport_service import get_vehicles, create_vehicle, get_routes, create_route, get_drivers, create_driver
from app.schemas.transport import Vehicle, VehicleCreate, Route, RouteCreate, Driver, DriverCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/summary")
def transport_summary(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("transport.read"))):
    vehicles=get_vehicles(db,current_org.id); routes=get_routes(db,current_org.id); drivers=get_drivers(db,current_org.id); assigned={r.vehicle_id for r in routes if r.vehicle_id}
    return {"vehicles":len(vehicles),"routes":len(routes),"drivers":len(drivers),"assigned_vehicles":len(assigned),"available_vehicles":sum(v.id not in assigned for v in vehicles),"total_capacity":sum(v.capacity for v in vehicles)}

@router.get("/vehicles", response_model=List[Vehicle])
def read_vehicles(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("transport.read"))): return get_vehicles(db, current_org.id)
@router.post("/vehicles", response_model=Vehicle)
def create_vehicle_endpoint(vehicle_in: VehicleCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("transport.manage"))): return create_vehicle(db, vehicle_in, current_org.id, current_user.id)
@router.get("/routes", response_model=List[Route])
def read_routes(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("transport.read"))): return get_routes(db, current_org.id)
@router.post("/routes", response_model=Route)
def create_route_endpoint(route_in: RouteCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("transport.manage"))): return create_route(db, route_in, current_org.id, current_user.id)
@router.get("/drivers", response_model=List[Driver])
def read_drivers(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("transport.read"))): return get_drivers(db, current_org.id)
@router.post("/drivers", response_model=Driver)
def create_driver_endpoint(driver_in: DriverCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(require_permission("transport.manage"))): return create_driver(db, driver_in, current_org.id, current_user.id)
