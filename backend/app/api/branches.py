from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.org_service import get_branches, create_branch, update_branch, delete_branch
from app.schemas.branch import Branch, BranchCreate
from app.models.base import Organization, User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[Branch])
def read_branches(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization)
):
    return get_branches(db, organization_id=current_org.id)

@router.post("/", response_model=Branch)
def create_branch_endpoint(
    branch_in: BranchCreate,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user)
):
    return create_branch(db, branch_in, current_org.id, current_user.id)

@router.put("/{branch_id}", response_model=Branch)
def update_branch_endpoint(
    branch_id: UUID,
    branch_in: BranchCreate,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user)
):
    branch = update_branch(db, branch_id, branch_in, current_org.id, current_user.id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch

@router.delete("/{branch_id}")
def delete_branch_endpoint(
    branch_id: UUID,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user)
):
    if not delete_branch(db, branch_id, current_org.id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return {"message": "Branch deleted"}
