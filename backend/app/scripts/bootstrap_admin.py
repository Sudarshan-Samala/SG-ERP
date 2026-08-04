import sys

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.bootstrap import bootstrap_super_admin


def main() -> int:
    if not settings.BOOTSTRAP_ADMIN_EMAIL or not settings.BOOTSTRAP_ADMIN_PASSWORD:
        print(
            "Bootstrap skipped: BOOTSTRAP_ADMIN_EMAIL and "
            "BOOTSTRAP_ADMIN_PASSWORD must both be set.",
            file=sys.stderr,
        )
        return 2

    db = SessionLocal()
    try:
        result = bootstrap_super_admin(
            db,
            email=settings.BOOTSTRAP_ADMIN_EMAIL,
            password=settings.BOOTSTRAP_ADMIN_PASSWORD,
        )
    except Exception as exc:
        db.rollback()
        print(f"Bootstrap failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    finally:
        db.close()

    if result.created:
        print("Super Admin created successfully.")
    else:
        print(f"Bootstrap skipped: {result.reason}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
