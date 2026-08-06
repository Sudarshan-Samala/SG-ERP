from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.org_service import get_organizations, create_organization, update_organization, delete_organization
from app.schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from app.models.base import User
from uuid import UUID

router = APIRouter()


def _require_superuser(current_user: User):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _conflict(exc: ValueError):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/", response_model=List[Organization])
def read_organizations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_superuser(current_user)
    return get_organizations(db)


@router.post("/", response_model=Organization, status_code=status.HTTP_201_CREATED)
def create_org(org_in: OrganizationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_superuser(current_user)
    try:
        return create_organization(db, org_in, current_user.id)
    except ValueError as exc:
        _conflict(exc)


@router.put("/{org_id}", response_model=Organization)
def update_org(org_id: UUID, org_in: OrganizationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_superuser(current_user)
    try:
        org = update_organization(db, org_id, org_in, current_user.id)
    except ValueError as exc:
        _conflict(exc)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.delete("/{org_id}")
def delete_org(org_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_superuser(current_user)
    try:
        deleted = delete_organization(db, org_id, current_user.id)
    except ValueError as exc:
        _conflict(exc)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return {"message": "Organization deleted"}
