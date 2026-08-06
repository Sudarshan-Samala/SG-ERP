import re
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import User, Role, Branch
from app.schemas.user_management import UserCreate, UserUpdate
from app.services.auth import get_password_hash
from app.services.audit.audit_service import log_action
from app.services.session_service import revoke_all_sessions


def get_users(db: Session, organization_id: UUID):
    return db.query(User).filter(User.organization_id == organization_id).order_by(User.email).all()

def _relations(db, organization_id, branch_ids, role_ids):
    branch_ids=set(branch_ids or []);role_ids=set(role_ids or [])
    branches=db.query(Branch).filter(Branch.organization_id==organization_id,Branch.id.in_(branch_ids),Branch.is_active.is_(True)).all() if branch_ids else []
    roles=db.query(Role).filter(Role.organization_id==organization_id,Role.id.in_(role_ids)).all() if role_ids else []
    if len(branches)!=len(branch_ids):raise HTTPException(status_code=400,detail='Invalid, inactive or cross-tenant branch')
    if len(roles)!=len(role_ids):raise HTTPException(status_code=400,detail='Invalid or cross-tenant role')
    return branches,roles

def _strong(password):return bool(re.search(r'[a-z]',password) and re.search(r'[A-Z]',password) and re.search(r'\d',password) and re.search(r'[^A-Za-z0-9]',password))

def create_user(db: Session, user_in: UserCreate, organization_id: UUID, actor_id: UUID):
    if not _strong(user_in.password):raise HTTPException(status_code=422,detail='Password must include uppercase, lowercase, number and special character')
    email=str(user_in.email).strip().lower();full_name=' '.join((user_in.full_name or '').split()) or None
    if db.query(User).filter(func.lower(User.email)==email).first():raise HTTPException(status_code=409,detail='User email already exists')
    branches,roles=_relations(db,organization_id,user_in.branch_ids,user_in.role_ids)
    user=User(email=email,hashed_password=get_password_hash(user_in.password),full_name=full_name,organization_id=organization_id,is_active=user_in.is_active,branches=branches,roles=roles);db.add(user)
    try:
        db.flush();log_action(db,organization_id,actor_id,'CREATE','USER',user.id,new_values=f'email={email}; active={user.is_active}');db.commit();db.refresh(user);return user
    except IntegrityError:db.rollback();raise HTTPException(status_code=409,detail='User email already exists')
    except Exception:db.rollback();raise

def update_user(db:Session,user_id:UUID,user_in:UserUpdate,organization_id:UUID,actor_id:UUID):
    user=db.query(User).filter(User.id==user_id,User.organization_id==organization_id).with_for_update().first()
    if not user:raise HTTPException(status_code=404,detail='User not found')
    if user.id==actor_id and user_in.is_active is False:raise HTTPException(status_code=409,detail='You cannot deactivate your own account')
    old=f'email={user.email}; active={user.is_active}'
    if user_in.email is not None:
        email=str(user_in.email).strip().lower();existing=db.query(User).filter(func.lower(User.email)==email,User.id!=user.id).first()
        if existing:raise HTTPException(status_code=409,detail='User email already exists')
        user.email=email
    if user_in.full_name is not None:user.full_name=' '.join(user_in.full_name.split()) or None
    if user_in.is_active is not None:user.is_active=user_in.is_active
    if user_in.branch_ids is not None or user_in.role_ids is not None:
        branches,roles=_relations(db,organization_id,user_in.branch_ids if user_in.branch_ids is not None else [b.id for b in user.branches],user_in.role_ids if user_in.role_ids is not None else [r.id for r in user.roles]);user.branches=branches;user.roles=roles
    try:
        db.flush();log_action(db,organization_id,actor_id,'UPDATE','USER',user.id,old_values=old,new_values=f'email={user.email}; active={user.is_active}');db.commit();db.refresh(user)
        if not user.is_active:revoke_all_sessions(db,user_id=user.id,organization_id=organization_id)
        return user
    except IntegrityError:db.rollback();raise HTTPException(status_code=409,detail='User email already exists')
    except Exception:db.rollback();raise
