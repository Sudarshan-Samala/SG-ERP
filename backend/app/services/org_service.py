from sqlalchemy.orm import Session
from app.models.base import Organization, Branch
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.branch import BranchCreate
from app.services.audit.audit_service import log_action
from uuid import UUID

# Organization CRUD
def get_organizations(db: Session):
    return db.query(Organization).all()

def get_organization(db: Session, org_id: UUID):
    return db.query(Organization).filter(Organization.id == org_id).first()

def create_organization(db: Session, org_in: OrganizationCreate, user_id: UUID):
    org = Organization(name=org_in.name, is_active=org_in.is_active)
    db.add(org)
    db.commit()
    db.refresh(org)
    log_action(db, org.id, user_id, "CREATE", "ORGANIZATION", org.id, new_values=str(org_in.dict()))
    return org

def update_organization(db: Session, org_id: UUID, org_in: OrganizationUpdate, user_id: UUID):
    org = get_organization(db, org_id)
    if not org:
        return None
    previous_values = str(org.__dict__)
    for field, value in org_in.dict(exclude_unset=True).items():
        setattr(org, field, value)
    db.commit()
    db.refresh(org)
    log_action(db, org.id, user_id, "UPDATE", "ORGANIZATION", org.id, previous_values=previous_values, new_values=str(org_in.dict(exclude_unset=True)))
    return org

def delete_organization(db: Session, org_id: UUID, user_id: UUID):
    org = get_organization(db, org_id)
    if not org:
        return False
    db.delete(org)
    db.commit()
    log_action(db, org.id, user_id, "DELETE", "ORGANIZATION", org_id)
    return True

# Branch CRUD (Tenant Scoped)
def get_branches(db: Session, organization_id: UUID):
    return db.query(Branch).filter(Branch.organization_id == organization_id).all()

def get_branch(db: Session, branch_id: UUID, organization_id: UUID):
    return db.query(Branch).filter(Branch.id == branch_id, Branch.organization_id == organization_id).first()

def create_branch(db: Session, branch_in: BranchCreate, organization_id: UUID, user_id: UUID):
    branch = Branch(
        name=branch_in.name,
        code=branch_in.code,
        is_active=branch_in.is_active,
        organization_id=organization_id,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    log_action(db, organization_id, user_id, "CREATE", "BRANCH", branch.id, new_values=str(branch_in.dict()))
    return branch

def update_branch(db: Session, branch_id: UUID, branch_in: BranchCreate, organization_id: UUID, user_id: UUID):
    branch = get_branch(db, branch_id, organization_id)
    if not branch:
        return None
    previous_values = str(branch.__dict__)
    for field, value in branch_in.dict(exclude_unset=True).items():
        setattr(branch, field, value)
    db.commit()
    db.refresh(branch)
    log_action(db, organization_id, user_id, "UPDATE", "BRANCH", branch.id, previous_values=previous_values, new_values=str(branch_in.dict(exclude_unset=True)))
    return branch

def delete_branch(db: Session, branch_id: UUID, organization_id: UUID, user_id: UUID):
    branch = get_branch(db, branch_id, organization_id)
    if not branch:
        return False
    db.delete(branch)
    db.commit()
    log_action(db, organization_id, user_id, "DELETE", "BRANCH", branch_id)
    return True
