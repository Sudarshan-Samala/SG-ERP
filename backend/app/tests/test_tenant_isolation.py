from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.core.database import SessionLocal, clear_current_tenant, set_current_tenant
from app.models.base import AcademicYear, Organization


def test_tenant_scope_blocks_cross_tenant_reads_and_writes():
    db = SessionLocal()
    org_a = Organization(name=f"tenant-a-{uuid4()}")
    org_b = Organization(name=f"tenant-b-{uuid4()}")
    db.add_all([org_a, org_b])
    db.flush()

    now = datetime.utcnow()
    year_a = AcademicYear(
        organization_id=org_a.id,
        name="2026-27-A",
        start_date=now,
        end_date=now + timedelta(days=365),
    )
    year_b = AcademicYear(
        organization_id=org_b.id,
        name="2026-27-B",
        start_date=now,
        end_date=now + timedelta(days=365),
    )
    db.add_all([year_a, year_b])
    db.commit()

    try:
        set_current_tenant(org_a.id)

        visible = db.query(AcademicYear).all()
        assert {row.organization_id for row in visible} == {org_a.id}
        assert db.query(AcademicYear).filter(AcademicYear.id == year_b.id).first() is None

        year_a.organization_id = org_b.id
        with pytest.raises(ValueError, match="Cross-tenant write denied"):
            db.commit()
        db.rollback()
    finally:
        clear_current_tenant()
        db.query(AcademicYear).filter(AcademicYear.id.in_([year_a.id, year_b.id])).delete(
            synchronize_session=False
        )
        db.query(Organization).filter(Organization.id.in_([org_a.id, org_b.id])).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()
