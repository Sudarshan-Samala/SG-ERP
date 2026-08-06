# SG-ERP Production Readiness Audit

Status: IN PROGRESS

Audit baseline: latest `main` at audit start.

## Release gates

SG-ERP must not be classified production-ready until all P0 gates are satisfied.

### P0-01 — Cross-tenant isolation

Every school-owned resource must be constrained by the authenticated organization/tenant at the data-access layer. A valid resource identifier must never be sufficient to access another school's data.

Required coverage includes direct CRUD, search, exports, reports, files, analytics, background jobs, notifications, integrations, and relationship lookups.

Required executable tests must use at least two organizations with overlapping human-facing identifiers and prove School A cannot read, mutate, delete, export, or infer School B records.

### P0-02 — Platform authority vs school authority

`is_superuser` currently represents platform bootstrap authority and bypasses ordinary permission/branch checks. Platform authority must not be treated as an implicit right to browse or mutate customer operational data.

Target model:

- Platform Super Admin: SaaS control-plane administration.
- School Admin: broad authority inside one tenant only.
- Platform Support: no implicit customer-data access; any future support access must be explicit, time-bound, purpose-bound, and audited.

### P0-03 — Branch isolation

Branch-scoped users must be prevented from crossing branch boundaries unless their assigned scope explicitly permits it. Branch identifiers must also be validated as belonging to the authenticated tenant.

### P0-04 — RBAC and privilege escalation

Permissions must be enforced server-side. Tests must cover unauthorized create/read/update/delete/export operations, role mutation, self-escalation, assignment of privileged roles, and attempts to expand organizational/branch scope.

### P0-05 — IDOR/BOLA resistance

All endpoints accepting object IDs require authorization against the object's tenant and applicable scope. Tests must include guessed/known UUIDs and human-facing IDs.

### P0-06 — Authentication/session security

Validate refresh rotation/replay protection, CSRF enforcement, session revocation, password policy, login/signup rate limiting, disabled-user/disabled-organization handling, and privileged-account lifecycle. MFA remains a production hardening requirement for privileged accounts.

### P0-07 — Sensitive files and exports

Student documents, employee documents, payslips, receipts, reports, and exports must require authorization at access time. File URLs or export IDs must not bypass tenant/field permissions.

### P0-08 — Financial and payroll integrity

Fee, finance, refund, concession, payroll, vendor, budget, and accounting mutations require tenant enforcement, permissions, appropriate maker-checker controls, immutable audit history, and transaction-safe validation.

## Confirmed findings

### AUD-P0-001 — Global superuser bypass requires control-plane separation

Severity: P0 / architectural.

The authentication dependency verifies JWT organization/session/user consistency. Normal school signup creates an Organization Administrator with `is_superuser=False`. Deployment bootstrap creates the dedicated `is_superuser=True` account.

However, the superuser flag bypasses ordinary permission and branch checks and is referenced across operational ERP APIs. The bootstrap account is also associated with an Organization record (the first organization, or a generated `System` organization). This creates an unsafe coupling between platform authority and tenant operational authority for a multi-school SaaS.

Required remediation:

1. Define explicit platform-level authorization independent of school roles.
2. Remove implicit customer operational-data access from platform authority.
3. Keep School Admin tenant-bound even when highly privileged inside the school.
4. Introduce explicit audited support-access workflow later if operational support requires customer-data access.
5. Add regression tests proving platform-control permissions do not silently grant school-data CRUD access.

### AUD-P0-002 — Cross-tenant executable coverage is a release gate

Severity: P0 / verification gap.

Repository testing backlog identifies cross-tenant/branch isolation and RBAC privilege-escalation coverage as incomplete. This must be converted into executable CI tests before production certification.

## Audit sequence

1. Authentication and privileged identity model.
2. Tenant/branch dependencies and data-access patterns.
3. Students/Admissions/Attendance object authorization.
4. Fees/Finance/Payroll object authorization.
5. Reports/exports/files/search isolation.
6. Communications/background-job recipient isolation.
7. RBAC mutation and privilege escalation.
8. Frontend role/tenant boundary UX.
9. Database constraints/migrations/indexes.
10. CI, deployment, observability, backup/recovery and secrets.

## Production classification

Current classification: **NOT YET PRODUCTION READY**.

Reason: P0 SaaS isolation and privileged-access verification remain incomplete. Feature breadth does not override these release gates.
