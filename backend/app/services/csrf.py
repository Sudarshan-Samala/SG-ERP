import base64
import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Request, status

from app.core.config import settings

CSRF_TOKEN_MAX_AGE_SECONDS = 60 * 60


def _sign(payload: str) -> str:
    digest = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_csrf_token() -> str:
    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(32)
    payload = f"{issued_at}.{nonce}"
    return f"{payload}.{_sign(payload)}"


def _is_valid_signed_token(token: str) -> bool:
    try:
        issued_at_raw, nonce, signature = token.split(".", 2)
        issued_at = int(issued_at_raw)
    except (TypeError, ValueError):
        return False

    if not nonce or not signature:
        return False

    now = int(time.time())
    if issued_at > now + 60 or now - issued_at > CSRF_TOKEN_MAX_AGE_SECONDS:
        return False

    payload = f"{issued_at}.{nonce}"
    expected = _sign(payload)
    return hmac.compare_digest(signature, expected)


def set_csrf_cookie(response, token: str) -> None:
    # Keep the cookie for compatibility/diagnostics, but CSRF validation does not
    # depend on browser delivery of this API-domain cookie. This is important for
    # cross-site frontends such as Vercel -> Render.
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/",
    )


def clear_csrf_cookie(response) -> None:
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def require_csrf(request: Request) -> None:
    # Validate the signed token carried in the custom header. A malicious
    # cross-site origin cannot read the bootstrap response because CORS is
    # restricted to TRUSTED_ORIGINS, so it cannot obtain a valid token to forge
    # a state-changing request. No cookie round-trip is required.
    header_token = request.headers.get("X-CSRF-Token")
    if not header_token or not _is_valid_signed_token(header_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
