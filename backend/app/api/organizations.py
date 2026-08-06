from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.core.database import get_db
from app.models.base import User
from app.schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from app.services.org_service import create_organization, delete_organization, get_organizations, update_organization

router = APIRouter()


@router.get("/", response_model=List[Organization])
def read_organizations(db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    return get_organizations(db)


@router.post("/", response_model=Organization)
def create_org(org_in: OrganizationCreate, db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    return create_organization(db, org_in, current_user.id)


@router.put("/{org_id}", response_model=Organization)
def update_org(org_id: UUID, org_in: OrganizationUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    org = update_organization(db, org_id, org_in, current_user.id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.delete("/{org_id}")
def delete_org(org_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    if not delete_organization(db, org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return {"message": "Organization deleted"}
