from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Driver, Route, Vehicle
from app.schemas.transport import DriverCreate, RouteCreate, VehicleCreate
from app.services.audit.audit_service import log_action


def get_vehicles(db: Session, organization_id: UUID):
    return db.query(Vehicle).filter(Vehicle.organization_id == organization_id).order_by(Vehicle.number).all()


def create_vehicle(db: Session, vehicle_in: VehicleCreate, organization_id: UUID, user_id: UUID):
    number = vehicle_in.number.strip().upper()
    existing = db.query(Vehicle).filter(Vehicle.organization_id == organization_id, Vehicle.number == number).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vehicle number already exists")
    veh = Vehicle(**{**vehicle_in.model_dump(), "number": number}, organization_id=organization_id)
    db.add(veh)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vehicle number already exists") from exc
    db.refresh(veh)
    log_action(db, organization_id, user_id, "CREATE", "VEHICLE", veh.id, new_values=str(vehicle_in.model_dump()))
    return veh


def get_routes(db: Session, organization_id: UUID):
    return db.query(Route).filter(Route.organization_id == organization_id).order_by(Route.name).all()


def create_route(db: Session, route_in: RouteCreate, organization_id: UUID, user_id: UUID):
    name = route_in.name.strip()
    if route_in.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == route_in.vehicle_id, Vehicle.organization_id == organization_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="Vehicle does not belong to this organization")
        assigned = db.query(Route).filter(Route.organization_id == organization_id, Route.vehicle_id == route_in.vehicle_id).first()
        if assigned:
            raise HTTPException(status_code=409, detail="Vehicle is already assigned to another route")
    existing = db.query(Route).filter(Route.organization_id == organization_id, Route.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Route name already exists")
    rou = Route(**{**route_in.model_dump(), "name": name}, organization_id=organization_id)
    db.add(rou)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Route already exists") from exc
    db.refresh(rou)
    log_action(db, organization_id, user_id, "CREATE", "ROUTE", rou.id, new_values=str(route_in.model_dump()))
    return rou


def get_drivers(db: Session, organization_id: UUID):
    return db.query(Driver).filter(Driver.organization_id == organization_id).order_by(Driver.name).all()


def create_driver(db: Session, driver_in: DriverCreate, organization_id: UUID, user_id: UUID):
    name = driver_in.name.strip()
    license_number = driver_in.license_number.strip().upper()
    existing = db.query(Driver).filter(Driver.organization_id == organization_id, Driver.license_number == license_number).first()
    if existing:
        raise HTTPException(status_code=409, detail="Driver license number already exists")
    dri = Driver(**{**driver_in.model_dump(), "name": name, "license_number": license_number}, organization_id=organization_id)
    db.add(dri)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Driver license number already exists") from exc
    db.refresh(dri)
    log_action(db, organization_id, user_id, "CREATE", "DRIVER", dri.id, new_values=str(driver_in.model_dump()))
    return dri
