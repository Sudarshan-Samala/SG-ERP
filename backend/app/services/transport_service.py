from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import Driver, Route, Vehicle
from app.schemas.transport import DriverCreate, RouteCreate, VehicleCreate
from app.services.audit.audit_service import log_action

def get_vehicles(db:Session,organization_id:UUID):return db.query(Vehicle).filter(Vehicle.organization_id==organization_id).order_by(Vehicle.number).all()
def get_routes(db:Session,organization_id:UUID):return db.query(Route).filter(Route.organization_id==organization_id).order_by(Route.name).all()
def get_drivers(db:Session,organization_id:UUID):return db.query(Driver).filter(Driver.organization_id==organization_id).order_by(Driver.name).all()

def _commit_audited(db,organization_id,user_id,action,entity,obj,payload,conflict):
    try:
        db.flush();log_action(db,organization_id,user_id,action,entity,obj.id,new_values=str(payload));db.commit();db.refresh(obj);return obj
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail=conflict) from exc
    except Exception:db.rollback();raise

def create_vehicle(db:Session,vehicle_in:VehicleCreate,organization_id:UUID,user_id:UUID):
    number=vehicle_in.number.strip().upper();capacity=vehicle_in.capacity
    if not number:raise HTTPException(status_code=422,detail='Vehicle number is required')
    if capacity<=0 or capacity>200:raise HTTPException(status_code=422,detail='Vehicle capacity must be between 1 and 200')
    if db.query(Vehicle).filter(Vehicle.organization_id==organization_id,Vehicle.number==number).first():raise HTTPException(status_code=409,detail='Vehicle number already exists')
    veh=Vehicle(**{**vehicle_in.model_dump(),'number':number},organization_id=organization_id);db.add(veh);return _commit_audited(db,organization_id,user_id,'CREATE','VEHICLE',veh,vehicle_in.model_dump(),'Vehicle number already exists')

def create_route(db:Session,route_in:RouteCreate,organization_id:UUID,user_id:UUID):
    name=route_in.name.strip()
    if not name:raise HTTPException(status_code=422,detail='Route name is required')
    if route_in.vehicle_id:
        vehicle=db.query(Vehicle).filter(Vehicle.id==route_in.vehicle_id,Vehicle.organization_id==organization_id).with_for_update().first()
        if not vehicle:raise HTTPException(status_code=400,detail='Vehicle does not belong to this organization')
        if db.query(Route).filter(Route.organization_id==organization_id,Route.vehicle_id==route_in.vehicle_id).first():raise HTTPException(status_code=409,detail='Vehicle is already assigned to another route')
    if db.query(Route).filter(Route.organization_id==organization_id,Route.name==name).first():raise HTTPException(status_code=409,detail='Route name already exists')
    rou=Route(**{**route_in.model_dump(),'name':name},organization_id=organization_id);db.add(rou);return _commit_audited(db,organization_id,user_id,'CREATE','ROUTE',rou,route_in.model_dump(),'Route already exists')

def create_driver(db:Session,driver_in:DriverCreate,organization_id:UUID,user_id:UUID):
    name=driver_in.name.strip();license_number=driver_in.license_number.strip().upper()
    if not name or not license_number:raise HTTPException(status_code=422,detail='Driver name and license number are required')
    if db.query(Driver).filter(Driver.organization_id==organization_id,Driver.license_number==license_number).first():raise HTTPException(status_code=409,detail='Driver license number already exists')
    dri=Driver(**{**driver_in.model_dump(),'name':name,'license_number':license_number},organization_id=organization_id);db.add(dri);return _commit_audited(db,organization_id,user_id,'CREATE','DRIVER',dri,driver_in.model_dump(),'Driver license number already exists')
