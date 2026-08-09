# CORE-001.2 — Authorization Policy Engine

## Purpose

Establish a centralized, default-deny authorization boundary after CORE-001.1 authentication/session hardening.

## Policy rules

1. Authentication establishes the trusted user and tenant context; it does not grant business permissions.
2. Permissions are explicit strings such as `students.read` or `fees.payment.collect`.
3. Tenant-scoped roles are evaluated only when their `organization_id` is the authenticated organization; global roles may be used for platform-level policy.
4. Missing permissions fail with HTTP 403.
5. Super Admin remains a bootstrap compatibility override, but new business authorization should use explicit permissions.
6. Tenant IDs supplied by clients cannot override the authenticated tenant.
7. Branch-scoped resources are restricted to branches assigned to the authenticated user, except platform superusers.
8. Resource services must continue to scope database queries by authenticated organization ID.
9. UI visibility is advisory only; every protected API operation must enforce policy server-side.

## Current implementation

- `AuthorizationPolicy` centralizes permission, tenant, and branch decisions.
- `require_permission()` is the FastAPI default-deny dependency used by protected endpoints.
- Student operations already enforce branch scope in addition to permission checks.
- RBAC role creation and assignment remain tenant-bound and reject cross-tenant role IDs.

## Future extension points

The policy service is intentionally small so CORE-001.3 can add database-level tenant isolation without replacing the authorization API. Resource/action scopes, temporary grants, and segregation-of-duties controls can be layered on the same policy boundary.
