# CORE-001.3 — Database Tenant Isolation

## Goal

Prevent authenticated application requests from reading or mutating records belonging to another organization, even when an endpoint accidentally omits an explicit `organization_id` predicate.

## Enforcement

The backend establishes the authenticated organization in a request-scoped `ContextVar` after validating the access token, session, user, and organization.

SQLAlchemy ORM `SELECT`, `UPDATE`, and `DELETE` statements are then automatically constrained for mapped models that contain an `organization_id` column. This is defense in depth and does not replace endpoint authorization checks.

A `before_flush` guard rejects new, dirty, or deleted tenant-owned ORM objects whose `organization_id` does not match the active organization.

## Rules

1. The authenticated organization is the only tenant context trusted by application data access.
2. Client-supplied organization identifiers must not expand the active tenant scope.
3. Cross-tenant reads return no matching resource rather than another tenant's record.
4. Cross-tenant updates and deletes are blocked by the ORM scope.
5. Cross-tenant object writes fail with `Cross-tenant write denied`.
6. System/bootstrap operations that intentionally run without an authenticated tenant context remain available for migrations and platform administration.
7. Explicit endpoint-level organization and branch checks remain required for authorization and resource-scope decisions.

## Verification

`backend/app/tests/test_tenant_isolation.py` verifies that a tenant can only read its own academic-year records and cannot move a record into another tenant while an authenticated tenant context is active.
