from contextvars import ContextVar

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_current_tenant: ContextVar[object | None] = ContextVar("sg_erp_current_tenant", default=None)


def set_current_tenant(organization_id):
    return _current_tenant.set(organization_id)


def clear_current_tenant():
    _current_tenant.set(None)


def get_current_tenant():
    return _current_tenant.get()


def _tenant_mappers():
    for mapper in Base.registry.mappers:
        if "organization_id" in mapper.columns:
            yield mapper.class_


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_scope(execute_state):
    """Defense-in-depth tenant filter for ORM SELECT/UPDATE/DELETE statements."""
    tenant_id = get_current_tenant()
    if tenant_id is None or not (
        execute_state.is_select or execute_state.is_update or execute_state.is_delete
    ):
        return

    statement = execute_state.statement
    for model in _tenant_mappers():
        statement = statement.options(
            with_loader_criteria(
                model,
                lambda cls, tenant_id=tenant_id: cls.organization_id == tenant_id,
                include_aliases=True,
            )
        )
    execute_state.statement = statement


@event.listens_for(Session, "before_flush")
def _validate_tenant_writes(session, flush_context, instances):
    """Reject writes that would cross the active tenant boundary."""
    tenant_id = get_current_tenant()
    if tenant_id is None:
        return

    for obj in list(session.new) + list(session.dirty) + list(session.deleted):
        if not hasattr(obj, "organization_id"):
            continue
        organization_id = getattr(obj, "organization_id", None)
        if organization_id != tenant_id:
            raise ValueError("Cross-tenant write denied")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        clear_current_tenant()
        db.close()
