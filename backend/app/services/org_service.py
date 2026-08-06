from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.base import Organization, Branch
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.branch import BranchCreate
from app.services.audit.audit_service import log_action
from uuid import UUID


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_code(value: str) -> str:
    return value.strip().upper()


# Organization CRUD
def get_organizations(db: Session):
    return db.query(Organization).order_by(Organization.name.asc()).all()


def get_organization(db: Session, org_id: UUID, *, for_update: bool = False):
    query = db.query(Organization).filter(Organization.id == org_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def create_organization(db: Session, org_in: OrganizationCreate, user_id: UUID):
    name = _normalize_name(org_in.name)
    if not name:
        raise ValueError("Organization name is required")
    org = Organization(name=name, is_active=org_in.is_active)
    try:
        db.add(org)
        db.flush()
        log_action(db, org.id, user_id, "CREATE", "ORGANIZATION", org.id, new_values=str({"name": name, "is_active": org.is_active}))
        db.commit()
        db.refresh(org)
        return org
    except Exception:
        db.rollback()
        raise


def update_organization(db: Session, org_id: UUID, org_in: OrganizationUpdate, user_id: UUID):
    org = get_organization(db, org_id, for_update=True)
    if not org:
        return None
    previous_values = {"name": org.name, "is_active": org.is_active}
    updates = org_in.dict(exclude_unset=True)
    if "name" in updates:
        updates["name"] = _normalize_name(updates["name"])
        if not updates["name"]:
            raise ValueError("Organization name is required")
    try:
        for field, value in updates.items():
            setattr(org, field, value)
        db.flush()
        log_action(db, org.id, user_id, "UPDATE", "ORGANIZATION", org.id, previous_values=str(previous_values), new_values=str(updates))
        db.commit()
        db.refresh(org)
        return org
    except Exception:
        db.rollback()
        raise


def delete_organization(db: Session, org_id: UUID, user_id: UUID):
    org = get_organization(db, org_id, for_update=True)
    if not org:
        return False
    # Hard-deleting a tenant is unsafe once dependent ERP records exist. Only
    # permit deletion of a truly empty tenant; otherwise callers should disable it.
    if db.query(Branch.id).filter(Branch.organization_id == org_id).first():
        raise ValueError("Organization has branches; deactivate it instead of deleting")
    try:
        log_action(db, org.id, user_id, "DELETE", "ORGANIZATION", org_id, previous_values=str({"name": org.name, "is_active": org.is_active}))
        db.delete(org)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# Branch CRUD (Tenant Scoped)
def get_branches(db: Session, organization_id: UUID):
    return db.query(Branch).filter(Branch.organization_id == organization_id).order_by(Branch.name.asc()).all()


def get_branch(db: Session, branch_id: UUID, organization_id: UUID, *, for_update: bool = False):
    query = db.query(Branch).filter(Branch.id == branch_id, Branch.organization_id == organization_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def create_branch(db: Session, branch_in: BranchCreate, organization_id: UUID, user_id: UUID):
    name = _normalize_name(branch_in.name)
    code = _normalize_code(branch_in.code)
    if not name or not code:
        raise ValueError("Branch name and code are required")
    duplicate = db.query(Branch.id).filter(Branch.organization_id == organization_id, Branch.code == code).first()
    if duplicate:
        raise ValueError("Branch code already exists")
    branch = Branch(name=name, code=code, is_active=branch_in.is_active, organization_id=organization_id)
    try:
        db.add(branch)
        db.flush()
        log_action(db, organization_id, user_id, "CREATE", "BRANCH", branch.id, new_values=str({"name": name, "code": code, "is_active": branch.is_active}))
        db.commit()
        db.refresh(branch)
        return branch
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Branch already exists") from exc
    except Exception:
        db.rollback()
        raise


def update_branch(db: Session, branch_id: UUID, branch_in: BranchCreate, organization_id: UUID, user_id: UUID):
    branch = get_branch(db, branch_id, organization_id, for_update=True)
    if not branch:
        return None
    name = _normalize_name(branch_in.name)
    code = _normalize_code(branch_in.code)
    if not name or not code:
        raise ValueError("Branch name and code are required")
    duplicate = db.query(Branch.id).filter(Branch.organization_id == organization_id, Branch.code == code, Branch.id != branch_id).first()
    if duplicate:
        raise ValueError("Branch code already exists")
    previous_values = {"name": branch.name, "code": branch.code, "is_active": branch.is_active}
    updates = {"name": name, "code": code, "is_active": branch_in.is_active}
    try:
        for field, value in updates.items():
            setattr(branch, field, value)
        db.flush()
        log_action(db, organization_id, user_id, "UPDATE", "BRANCH", branch.id, previous_values=str(previous_values), new_values=str(updates))
        db.commit()
        db.refresh(branch)
        return branch
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Branch already exists") from exc
    except Exception:
        db.rollback()
        raise


def delete_branch(db: Session, branch_id: UUID, organization_id: UUID, user_id: UUID):
    branch = get_branch(db, branch_id, organization_id, for_update=True)
    if not branch:
        return False
    # Branches are tenant boundaries referenced throughout the ERP. Preserve
    # referential history by requiring deactivation rather than hard deletion.
    if branch.is_active:
        raise ValueError("Deactivate the branch before deleting it")
    try:
        log_action(db, organization_id, user_id, "DELETE", "BRANCH", branch_id, previous_values=str({"name": branch.name, "code": branch.code, "is_active": branch.is_active}))
        db.delete(branch)
        db.commit()
        return True
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Branch is referenced by ERP records; keep it inactive instead") from exc
    except Exception:
        db.rollback()
        raise
