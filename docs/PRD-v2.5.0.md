# SG ERP — Product Requirements Document

**Version:** 2.5.0  
**Status:** Implementation-Ready Foundation Baseline  
**Date:** 2026-08-03  
**Supersedes:** README PRD v2.4.0

## 1. Repository Reality

At this revision, the repository contains the product requirements baseline but no committed application scaffold, dependency manifest, migrations, backend entry point, frontend package manifest, or automated test suite. Therefore the previous concept of verifying an already-built platform foundation is not applicable yet.

The next engineering milestone is to create the development foundation first, then verify it.

## 2. Product Direction

SG ERP remains a modular ERP for finance, procurement, inventory, manufacturing, HR, assets, projects, support, reporting, and future assistive intelligence. The implementation must favor a clean core: domain logic stays independent from customer-specific extensions, integrations use released application contracts rather than direct database coupling, and cross-cutting capabilities are implemented once as shared platform services.

## 3. Architecture Principles

1. **Modular monolith first.** Start with clear domain boundaries in one deployable backend; split services only when operational evidence justifies it.
2. **API-first.** UI and integrations consume stable application APIs rather than database tables.
3. **Clean core.** Customizations use configuration, events, adapters, and explicit extension contracts.
4. **Tenant-aware from the foundation.** Tenant identity and isolation are platform concerns, not a Phase 4 retrofit.
5. **Default deny.** Authorization denies access unless an explicit valid grant applies.
6. **Transactional integrity.** Material commands are atomic, audited, concurrency-safe, and idempotent where retries are possible.
7. **Observable operations.** Requests, jobs, events, and failures carry correlation identifiers and structured telemetry.
8. **Upgrade-safe contracts.** Public APIs and business-event schemas are versioned and backward compatibility is governed.

## 4. Foundation Technology Baseline

The first implementation must establish a documented, reproducible development environment with:

- Backend application entry point and modular package structure
- Relational database connection and migration framework
- Environment-based configuration with no committed secrets
- Health and readiness endpoints
- Structured logging and request correlation ID
- Automated unit/integration test harness
- Linting and static/type checking
- Container-based local development path
- CI workflow that runs validation on pull requests

Exact framework/library versions must be pinned in the repository when the scaffold is created rather than being implied only by the PRD.

## 5. Multi-Tenancy Correction

Multi-tenancy moves from the old Phase 4 roadmap into Phase 1 foundation design.

Initial requirements:

- Tenant is resolved from a trusted server-side mechanism.
- Tenant-owned records use non-null tenant identity where applicable.
- Repository/service queries are tenant scoped by default.
- Cross-tenant foreign references are rejected.
- Authentication sessions bind to tenant context.
- Authorization evaluates tenant and resource scope.
- Automated negative tests prove Tenant A cannot read or mutate Tenant B data.

This does not require advanced tenant billing, tenant self-service, or multi-region tenancy in the first release.

## 6. Authentication and Authorization

Foundation security is delivered incrementally after the scaffold.

### Authentication

- Secure password hashing
- Login and logout
- Short-lived access token
- Refresh-token family and rotation
- Refresh replay detection
- Session revocation
- Authentication rate limiting/abuse protection
- Security events without token/credential leakage

### Authorization

Core model:

- Permission
- Role
- RolePermission
- UserRole
- ResourceScope
- AuthorizationDecision
- AuthorizationService

Role assignments should support `valid_from`, `valid_until`, and active state so temporary access can be added without redesigning the schema. Missing, expired, inactive, cross-tenant, or out-of-scope grants resolve to DENY.

Future governance may add duties, segregation-of-duties rules, access certification, and privileged temporary access without expanding the first authorization sprint.

## 7. Transaction Integrity

Material ERP operations must use explicit transaction boundaries. Mutable business aggregates use optimistic concurrency/version checks to prevent lost updates. Retryable create/action commands such as receipts, invoices, payments, production confirmations, inventory adjustments, and accounting postings support idempotency keys.

Idempotency and concurrency are separate controls: idempotency prevents duplicate execution; optimistic concurrency prevents stale writes.

## 8. Events and Background Work

Business events use versioned schemas and unique event IDs. Event publication should use a transactional outbox so a committed business transaction cannot silently lose its event. Consumers must tolerate duplicate delivery and must not assume asynchronous delivery order.

Background work uses a common lifecycle with queued, running, succeeded, retry-wait, failed, cancelled, and dead-lettered states. Retry policy distinguishes transient failures from permanent/business errors.

## 9. Configuration and Extensibility

Material configuration is versioned and effective-dated rather than overwritten in place. Configuration changes preserve actor, approval, effective date, previous value/version, and audit metadata.

Supported extension surfaces should evolve through:

- Configuration
- Feature flags
- Custom fields
- Versioned business events
- Webhooks
- Report/document templates
- Released extension APIs

Extensions must not require modification of domain core code for routine customer customization.

## 10. Master Data Governance

Customer, supplier, item/product, and key financial masters require governed lifecycle states, duplicate checks, blocking instead of destructive deletion when historical transactions exist, and audit history. Future consolidation supports canonical/golden records and survivorship rules.

Transactional modules must not silently create governed master data unless an explicitly authorized import/integration workflow performs that creation.

## 11. Financial Controls

Finance design must support control accounts, subledger-to-GL traceability, reconciliation, period state transitions, controlled reopen, and close validation. A period is not considered closed merely because a status field changed; required validations and close tasks must succeed.

## 12. Data Lifecycle

Archive and deletion are distinct operations. Retention is policy-driven and may depend on legal entity, jurisdiction, object type, and business event. Active legal holds prevent destruction. Critical accounting/audit records are immutable during their governed retention lifecycle but are not automatically defined as permanent forever-retention records.

## 13. Integration Governance

External integrations use explicit client identity, least-privilege scopes, versioned APIs/events, throttling, retry semantics, external-object identity mapping, and observability. Bulk operations should be asynchronous when synchronous per-record calls would create excessive load.

No supported integration may depend on direct production database access.

## 14. Revised Delivery Roadmap

### Phase 0 — Engineering Foundation

- CORE-000.1 Repository/Application Scaffold
- CORE-000.2 Foundation Verification

### Phase 1 — Security and Organization

- CORE-001.1 Tenant-Aware Authentication & Sessions
- CORE-001.2 Authorization Policy Engine
- CORE-001.3 Database Tenant Isolation
- CORE-002 Organization Structure

### Phase 2 — Shared ERP Platform

- Workflow/approvals
- Audit
- Transaction integrity
- Configuration/feature management
- Events/background jobs
- Notifications
- Document/report foundation

### Phase 3 — Business Domains

- Master data
- Finance
- Procurement
- Inventory/WMS
- Assets
- HR
- Projects
- Support
- Manufacturing/quality as prioritized

### Phase 4 — Scale and Intelligence

- Advanced analytics
- AI-assisted summaries and exception handling
- Forecasting
- Advanced integration/extensibility
- Mobile applications where justified

## 15. Next Implementation-Ready Task — CORE-000.1

### Repository/Application Scaffold

**Priority:** P0  
**Goal:** Turn the PRD-only repository into a reproducible development project without implementing business modules.

### Scope

1. Establish backend and frontend project roots.
2. Add pinned dependency manifests and documented runtime versions.
3. Add backend application entry point.
4. Add environment configuration and `.env.example` containing placeholders only.
5. Add relational database setup and initial migration framework.
6. Add `/health` and `/ready` endpoints.
7. Add request correlation-ID middleware and structured logging baseline.
8. Add unit/integration test harness with at least health/readiness tests.
9. Add lint/type/static-check configuration.
10. Add local container/development configuration.
11. Add CI validation for tests, lint/type checks, and migration sanity.
12. Document local setup in the repository.

### Explicitly Out of Scope

- Production deployment
- Production credentials
- Business modules
- Full authentication
- RBAC implementation
- AI features
- Kubernetes/microservices
- Premature service decomposition

### Acceptance Criteria

- A fresh checkout can install dependencies from documented instructions.
- The backend starts successfully in development mode.
- `/health` returns success when the process is alive.
- `/ready` reports dependency readiness and fails appropriately when required dependencies are unavailable.
- A clean development database can apply migrations from zero.
- Tests pass from a clean checkout.
- Lint/type/static checks pass.
- No secrets are committed.
- CI runs the foundation checks on pull requests.
- No production environment is changed.

## 16. Prepared Next Task — CORE-000.2

### Foundation Verification

After CORE-000.1 is merged, generate a verification report containing:

- commit SHA
- runtime/dependency installation result
- clean migration result
- application startup result
- health result
- readiness result
- automated test result
- lint result
- type/static-check result
- secret/security sanity result
- verification timestamp

Only PASS closes the foundation gate. Failure creates the smallest corrective defect and the verification is repeated.

## 17. Task After the Foundation Gate

Once CORE-000.2 passes, begin **CORE-001.1 Tenant-Aware Authentication & Sessions**. Do not pull authorization, segregation of duties, business modules, or advanced integration infrastructure into that sprint.

## 18. Definition of Ready

A task is ready when business intent, scope, acceptance criteria, data impact, API impact, permissions, migration impact, negative tests, and explicit non-goals are known.

## 19. Definition of Done

A task is done only when implementation, review, tests, migrations, security checks, audit requirements, API/documentation updates, and relevant operational diagnostics are complete. Passing locally is insufficient when CI is required by the task.

## 20. Production Safety Rule

Development, testing, migrations, and verification for these foundation tasks must use development/test infrastructure only. No task in this PRD authorizes production deployment or production data modification.
