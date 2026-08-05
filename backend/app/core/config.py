from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sampurna Gnana ERP"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_COOKIE_NAME: str = "sg_refresh"
    REFRESH_COOKIE_SECURE: bool = True
    REFRESH_COOKIE_SAMESITE: str = "lax"
    CSRF_COOKIE_NAME: str = "sg_csrf"
    TRUSTED_ORIGINS: list[str] = []
    AUTH_LOGIN_RATE_LIMIT: int = 10
    AUTH_REFRESH_RATE_LIMIT: int = 30
    AUTH_SIGNUP_RATE_LIMIT: int = 5
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    BOOTSTRAP_ADMIN_EMAIL: Optional[str] = None
    BOOTSTRAP_ADMIN_PASSWORD: Optional[str] = None

    @field_validator("TRUSTED_ORIGINS", mode="before")
    @classmethod
    def parse_trusted_origins(cls, value):
        if isinstance(value, str): return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("REFRESH_COOKIE_SAMESITE")
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}: raise ValueError("REFRESH_COOKIE_SAMESITE must be lax, strict, or none")
        return normalized

    class Config: env_file = ".env"

settings = Settings()
