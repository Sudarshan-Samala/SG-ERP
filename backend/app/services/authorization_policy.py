from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import User


class AuthorizationPolicy:
    """Central authorization policy for tenant and branch-scoped decisions."""

    @staticmethod
    def permissions_for(user: User) -> set[str]:
        if user.is_superuser:
            return {"*"}
        return {
            permission.name
            for role in user.roles
            if role.organization_id in (None, user.organization_id)
            for permission in role.permissions
        }

    @classmethod
    def allows(cls, user: User, permission: str) -> bool:
        permissions = cls.permissions_for(user)
        return "*" in permissions or permission in permissions

    @classmethod
    def require(cls, user: User, permission: str) -> User:
        if not cls.allows(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )
        return user

    @staticmethod
    def require_tenant(user: User, organization_id: UUID | None) -> User:
        if organization_id is not None and organization_id != user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access denied",
            )
        return user

    @staticmethod
    def require_branch(db: Session, user: User, branch_id: UUID | None) -> User:
        if branch_id is None or user.is_superuser:
            return user
        allowed = any(
            branch.id == branch_id and branch.organization_id == user.organization_id
            for branch in user.branches
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Branch access denied",
            )
        return user
