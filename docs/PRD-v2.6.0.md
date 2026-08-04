# SG ERP — Product Requirements Document

**Version:** 2.6.0  
**Status:** Authentication & Session Implementation Baseline  
**Date:** 2026-08-04  
**Supersedes:** PRD v2.5.0

## 1. Repository Reality

The repository has advanced beyond the PRD-only state described in v2.5. It now contains a FastAPI backend, Next.js frontend, relational models/migrations, multiple school ERP domain APIs, an `/health` endpoint, an authentication login endpoint under `/api/v1/auth/login`, and a secure, idempotent first-Super-Admin bootstrap merged through PR #5.

The current authentication implementation issues a single access token after email/password verification. It does not yet implement the session lifecycle required by the product baseline: refresh-token rotation, replay detection, logout/session revocation, tenant-bound sessions, or authentication abuse controls. The backend CORS configuration also currently permits `*` while credentials are enabled and must be replaced by an environment-specific allowlist before browser credential flows are relied upon.

Therefore the next implementation-ready task is **CORE-001.1 Tenant-Aware Authentication & Sessions**. Foundation verification remains a release gate, but should now verify the actual implementation rather than block preparation of the security sprint.

## 2. Product Direction

SG ERP remains a modular ERP for school and general enterprise operations. The implementation follows a modular-monolith-first, API-first, clean-core approach. Shared security, tenancy, audit, workflow, configuration, reporting, events, and observability capabilities are platform services rather than duplicated inside business modules.

## 3. Architecture and ERP Control Principles

1. **Tenant-aware by default.** Tenant identity is derived from trusted server-side/session context and never trusted solely from a client-supplied tenant ID.
2. **Default-deny authorization.** Authentication proves identity; authorization separately decides whether the authenticated principal may perform an action.
3. **Server-enforced workflow state.** Material ERP state transitions are validated on the backend; UI sequencing is never a security control.
4. **Transactional integrity.** Material commands are atomic, audited, concurrency-safe, and idempotent where retries are possible.
5. **Least privilege and segregation readiness.** Roles/permissions must support future segregation-of-duties controls without schema replacement.
6. **Immutable business evidence.** Audit/security events preserve actor, tenant, action, outcome, timestamp, correlation ID, and relevant object identity without recording credentials or tokens.
7. **Clean extension surfaces.** Integrations use versioned APIs/events, not direct production database coupling.
8. **Operational observability.** Requests, jobs, events, and failures carry correlation identifiers and structured telemetry.

## 4. Authentication & Session Security Baseline

### 4.1 Login

- Canonical endpoint: `POST /api/v1/auth/login`.
- Preserve a generic invalid-credential response so account existence is not disclosed.
- Normalize login identifiers consistently.
- Successful login creates a server-tracked session and binds it to user and tenant/organization context.
- Authentication events are recorded without plaintext passwords or token values.

### 4.2 Token and Session Model

Use a short-lived access token plus a long-lived refresh credential/session record.

Minimum session fields:

- `id` (UUID)
- `user_id`
- `organization_id` / tenant identity
- refresh-token family identifier
- hash/fingerprint of the active refresh credential; never persist the plaintext refresh token
- `created_at`
- `last_used_at`
- `expires_at`
- `revoked_at`
- revocation reason
- optional client/device metadata limited to operational need

Access tokens must include only the claims required by the API, including subject, tenant/session identity, issued/expiry times, and a unique token identifier where useful. Authorization data that changes frequently should not become an indefinitely stale token truth source.

### 4.3 Refresh Rotation and Replay Detection

- Every successful refresh rotates the refresh credential.
- A previously consumed refresh credential cannot be used again.
- Reuse/replay of a rotated credential revokes the affected token family/session and records a security event.
- Refresh operations are concurrency-safe so two simultaneous refresh attempts cannot both succeed.
- Expired, revoked, malformed, cross-tenant, or unknown sessions fail closed.

### 4.4 Logout and Revocation

Provide:

- logout current session
- revoke a specific session
- revoke all sessions for the current user
- administrative revocation capability later through authorization policy

Password reset/change and high-risk privilege changes must support revoking or renewing existing sessions according to policy.

### 4.5 Browser Credential Handling

Authentication/session credentials must not be stored in browser `localStorage` or `sessionStorage`. Prefer `HttpOnly`, `Secure`, appropriately scoped `SameSite` cookies for refresh/session credentials, with CSRF protection where cookie-based authenticated state-changing requests require it. Short-lived access tokens should have the smallest practical browser exposure.

### 4.6 CORS

Replace wildcard CORS with configuration-driven explicit trusted origins for development, preview/staging, and production. Credentialed browser access must never depend on `allow_origins=["*"]`. CORS is not an authorization mechanism.

### 4.7 Abuse Protection

- Rate-limit login and refresh endpoints using both account-aware and source-aware signals where practical.
- Return `429` for throttled requests.
- Avoid permanent account lockout patterns that enable trivial denial of service.
- Record repeated authentication failures as security telemetry without exposing sensitive values.

## 5. Tenant Isolation Requirements

- A session is bound to exactly one tenant/organization context unless an explicitly designed privileged cross-tenant workflow exists.
- Protected repositories/services scope tenant-owned queries by authenticated tenant context.
- Client-supplied organization IDs never override the authenticated tenant context.
- Cross-tenant references and mutations are rejected.
- Negative tests must prove Tenant A cannot read, mutate, refresh, revoke, or otherwise act on Tenant B resources/sessions.

Database-enforced tenant isolation remains **CORE-001.3**; CORE-001.1 must establish the trusted tenant context consumed by that later control.

## 6. Authorization Boundary

CORE-001.1 authenticates identity and establishes trusted tenant/session context. It does not implement the full permission policy engine. Full RBAC/policy evaluation, temporary grants, resource scopes, and default-deny authorization enforcement are **CORE-001.2**.

Existing `is_superuser` behavior may remain for bootstrap compatibility but must not become the long-term substitute for explicit authorization policy.

## 7. API Contract for CORE-001.1

Required operations:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/logout-all`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`

Exact request/response schemas must be documented in OpenAPI. Sensitive responses use `Cache-Control: no-store`. Errors use semantically appropriate HTTP status codes and do not reveal internal stack traces, hashes, secrets, or token material.

## 8. Data and Migration Requirements

CORE-001.1 may add session/refresh-token and security-event persistence through Alembic migrations. Migrations must:

- apply from a clean development/test database;
- upgrade from the current schema;
- preserve existing users and the bootstrap Super Admin;
- contain no environment-specific credentials;
- define indexes/constraints for session lookup, expiry, token-family uniqueness, and tenant/user scoping as appropriate.

No production migration is authorized by this PRD.

## 9. Audit and Security Events

Capture at minimum:

- login success/failure
- refresh success/failure/replay detection
- logout
- session revocation
- logout-all
- disabled/inactive-user authentication attempts

Events include actor/user identity when known, tenant, session ID where applicable, event type, outcome, timestamp, correlation ID, and sanitized context. Never record plaintext passwords, access tokens, refresh tokens, secret keys, or full credential hashes usable for authentication.

## 10. Acceptance Criteria — CORE-001.1

1. Valid credentials create an authenticated, tenant-bound session.
2. Invalid credentials return a generic authentication failure.
3. Inactive users cannot create or refresh sessions.
4. Access tokens expire according to configuration.
5. Refresh succeeds once and rotates the refresh credential.
6. Reuse of an already-rotated refresh credential is detected and invalidates the affected session/family.
7. Logout revokes the current session; logout-all revokes all active sessions for that user.
8. A revoked or expired session cannot refresh.
9. Tenant A cannot operate on Tenant B sessions/resources covered by this task.
10. Browser refresh/session credentials are not persisted in Web Storage.
11. CORS uses explicit configured trusted origins; wildcard credentialed CORS is removed.
12. Login/refresh abuse controls are tested, including a `429` path.
13. Security events are emitted without credential/token leakage.
14. Alembic migrations apply successfully to clean and current development/test schemas.
15. Unit/integration tests cover success, failure, expiry, rotation, replay, revocation, concurrency, and cross-tenant negative cases.
16. OpenAPI and environment-variable documentation are updated.
17. No production deployment, production migration, or production secret modification occurs.

## 11. Explicit Non-Goals — CORE-001.1

- Public self-registration
- Full RBAC/policy engine
- Segregation-of-duties engine
- SSO/OIDC/SAML
- MFA implementation
- Passwordless authentication
- Business-module redesign
- Production deployment

## 12. Next Tasks

After CORE-001.1 passes review and verification:

1. **CORE-001.2 Authorization Policy Engine** — explicit permissions, roles, resource scopes, default deny, tenant-aware decisions, authorization tests.
2. **CORE-001.3 Database Tenant Isolation** — enforce tenant ownership/integrity at repository and database layers with cross-tenant negative tests.
3. **CORE-002 Organization Structure** — governed organization/branch/department hierarchy built on the trusted tenant/security foundation.

## 13. Foundation Verification Update

CORE-000.2 is retained as a quality gate and should verify the current repository: dependency installation, migration-from-zero, application startup, `/health`, readiness behavior, tests, lint/static checks, secret sanity, CORS configuration, and CI status. Any missing foundation item should become a narrowly scoped defect rather than reverting the repository to the old PRD-only milestone.

## 14. Definition of Ready

A task is ready when business intent, API contract, data impact, tenant behavior, authorization boundary, migration impact, audit/security events, acceptance criteria, negative tests, operational diagnostics, and explicit non-goals are defined.

## 15. Definition of Done

A task is done only when implementation, review, automated tests, migrations, security checks, audit requirements, OpenAPI/documentation updates, and operational diagnostics are complete. CI-required work is not done merely because it passes locally.

## 16. Production Safety Rule

All implementation, migration testing, bootstrap testing, and verification described here must use development/test infrastructure unless a separately approved production change exists. This PRD does not authorize production deployment or production data modification.
