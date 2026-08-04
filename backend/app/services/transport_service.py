from sqlalchemy.orm import Session
from app.models.base import Vehicle, Route, Driver
from app.schemas.transport import VehicleCreate, RouteCreate, DriverCreate
from app.services.audit.audit_service import log_action
from uuid import UUID
from typing import Optional

# Vehicle
def get_vehicles(db: Session, organization_id: UUID):
    return db.query(Vehicle).filter(Vehicle.organization_id == organization_id).all()

def create_vehicle(db: Session, vehicle_in: VehicleCreate, organization_id: UUID, user_id: UUID):
    veh = Vehicle(**vehicle_in.model_dump(), organization_id=organization_id)
    db.add(veh)
    db.commit()
    db.refresh(veh)
    log_action(db, organization_id, user_id, "CREATE", "VEHICLE", veh.id, new_values=str(vehicle_in.model_dump()))
    return veh

# Route
def get_routes(db: Session, organization_id: UUID):
    return db.query(Route).filter(Route.organization_id == organization_id).all()

def create_route(db: Session, route_in: RouteCreate, organization_id: UUID, user_id: UUID):
    rou = Route(**route_in.model_dump(), organization_id=organization_id)
    db.add(rou)
    db.commit()
    db.refresh(rou)
    log_action(db, organization_id, user_id, "CREATE", "ROUTE", rou.id, new_values=str(route_in.model_dump()))
    return rou

# Driver
def get_drivers(db: Session, organization_id: UUID):
    return db.query(Driver).filter(Driver.organization_id == organization_id).all()

def create_driver(db: Session, driver_in: DriverCreate, organization_id: UUID, user_id: UUID):
    dri = Driver(**driver_in.model_dump(), organization_id=organization_id)
    db.add(dri)
    db.commit()
    db.refresh(dri)
    log_action(db, organization_id, user_id, "CREATE", "DRIVER", dri.id, new_values=str(driver_in.model_dump()))
    return dri
