from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auth_session import AuthSession
from app.models.base import User
from app.services.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub"); organization_id = payload.get("org"); session_id = payload.get("sid")
        if not user_id or not organization_id or not session_id: raise credentials_exception
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    session = db.query(AuthSession).filter(AuthSession.id == session_id, AuthSession.user_id == user_id, AuthSession.organization_id == organization_id, AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.utcnow()).first()
    if session is None: raise credentials_exception
    user = db.query(User).filter(User.id == user_id, User.organization_id == organization_id, User.is_active.is_(True)).first()
    if user is None: raise credentials_exception
    return user


def get_current_organization(current_user: User = Depends(get_current_user)):
    return current_user.organization


def require_permission(permission_name: str):
    """Default-deny RBAC dependency. Superusers bypass role permission checks."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        permissions = {permission.name for role in current_user.roles for permission in role.permissions}
        if permission_name not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return current_user
    return dependency


def accessible_branch_ids(current_user: User) -> set[UUID]:
    """Return explicitly assigned branches. Superusers are unrestricted."""
    if current_user.is_superuser:
        return set()
    return {branch.id for branch in current_user.branches if branch.organization_id == current_user.organization_id}


def enforce_branch_access(current_user: User, branch_id: UUID) -> None:
    """Default-deny branch authorization for non-superusers."""
    if current_user.is_superuser:
        return
    if branch_id not in accessible_branch_ids(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch access denied")
