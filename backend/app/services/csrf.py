import hmac
import secrets

from fastapi import HTTPException, Request, status

from app.core.config import settings


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response, token: str) -> None:
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
    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
