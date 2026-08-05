from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import Driver, Route, Vehicle
from app.schemas.transport import DriverCreate, RouteCreate, VehicleCreate
from app.services.audit.audit_service import log_action


def get_vehicles(db: Session, organization_id: UUID):
    return db.query(Vehicle).filter(Vehicle.organization_id == organization_id).all()


def create_vehicle(db: Session, vehicle_in: VehicleCreate, organization_id: UUID, user_id: UUID):
    existing = db.query(Vehicle).filter(Vehicle.organization_id == organization_id, Vehicle.number == vehicle_in.number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle number already exists")
    veh = Vehicle(**vehicle_in.model_dump(), organization_id=organization_id)
    db.add(veh); db.commit(); db.refresh(veh)
    log_action(db, organization_id, user_id, "CREATE", "VEHICLE", veh.id, new_values=str(vehicle_in.model_dump()))
    return veh


def get_routes(db: Session, organization_id: UUID):
    return db.query(Route).filter(Route.organization_id == organization_id).all()


def create_route(db: Session, route_in: RouteCreate, organization_id: UUID, user_id: UUID):
    if route_in.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == route_in.vehicle_id, Vehicle.organization_id == organization_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle does not belong to this organization")
    rou = Route(**route_in.model_dump(), organization_id=organization_id)
    db.add(rou); db.commit(); db.refresh(rou)
    log_action(db, organization_id, user_id, "CREATE", "ROUTE", rou.id, new_values=str(route_in.model_dump()))
    return rou


def get_drivers(db: Session, organization_id: UUID):
    return db.query(Driver).filter(Driver.organization_id == organization_id).all()


def create_driver(db: Session, driver_in: DriverCreate, organization_id: UUID, user_id: UUID):
    existing = db.query(Driver).filter(Driver.organization_id == organization_id, Driver.license_number == driver_in.license_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Driver license number already exists")
    dri = Driver(**driver_in.model_dump(), organization_id=organization_id)
    db.add(dri); db.commit(); db.refresh(dri)
    log_action(db, organization_id, user_id, "CREATE", "DRIVER", dri.id, new_values=str(driver_in.model_dump()))
    return dri
