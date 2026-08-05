from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS, ROLE_PERMISSION_SETS
from app.models.base import Organization, Permission, Role


@dataclass(frozen=True)
class RbacBootstrapResult:
    permissions_created: int
    roles_created: int


def bootstrap_rbac(db: Session) -> RbacBootstrapResult:
    """Idempotently provision the permission catalog and built-in tenant roles."""
    created_permissions = 0
    permission_by_name = {p.name: p for p in db.query(Permission).all()}
    for name, description in PERMISSIONS.items():
        permission = permission_by_name.get(name)
        if permission is None:
            permission = Permission(name=name, description=description)
            db.add(permission)
            db.flush()
            permission_by_name[name] = permission
            created_permissions += 1
        elif permission.description != description:
            permission.description = description

    created_roles = 0
    for organization in db.query(Organization).all():
        for role_name, permission_names in ROLE_PERMISSION_SETS.items():
            role = db.query(Role).filter(Role.organization_id == organization.id, Role.name == role_name).first()
            if role is None:
                role = Role(organization_id=organization.id, name=role_name)
                db.add(role)
                db.flush()
                created_roles += 1
            # Built-in role definitions are authoritative and deterministic.
            role.permissions = [permission_by_name[name] for name in sorted(permission_names)]

    db.commit()
    return RbacBootstrapResult(created_permissions, created_roles)
