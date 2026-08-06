from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.user_management_service import get_users, create_user, update_user
from app.schemas.user_management import User, UserCreate, UserUpdate
from app.models.base import Organization

router = APIRouter()

@router.get('/', response_model=List[User])
def read_users(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user=Depends(require_permission('users.manage'))):
    return [User.from_model(u) for u in get_users(db,current_org.id)]

@router.post('/',response_model=User,status_code=201)
def create_user_endpoint(user_in:UserCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user=Depends(require_permission('users.manage'))):
    return User.from_model(create_user(db,user_in,current_org.id,current_user.id))

@router.patch('/{user_id}',response_model=User)
def update_user_endpoint(user_id:UUID,user_in:UserUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user=Depends(require_permission('users.manage'))):
    return User.from_model(update_user(db,user_id,user_in,current_org.id,current_user.id))
