import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    *,
    organization_id: Optional[Union[str, Any]] = None,
    session_id: Optional[Union[str, Any]] = None,
) -> str:
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "sub": str(subject),
    }
    if organization_id is not None:
        to_encode["org"] = str(organization_id)
    if session_id is not None:
        to_encode["sid"] = str(session_id)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_refresh_token() -> str:
    """Return a cryptographically secure opaque refresh credential."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Create a keyed, one-way digest suitable for database persistence."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def refresh_token_matches(token: str, stored_digest: str) -> bool:
    """Constant-time comparison of a presented refresh token to its digest."""
    return hmac.compare_digest(hash_refresh_token(token), stored_digest)
