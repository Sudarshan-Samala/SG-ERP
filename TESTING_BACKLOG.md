# Sampurna Gnana ERP - Testing Backlog

This file tracks remaining non-blocking security and QA work after the production-hardening batches.

| Module | Issue Description | Severity | Status |
| :--- | :--- | :--- | :--- |
| Foundation | MFA / TOTP enrollment and recovery is not yet implemented | High | Open |
| Foundation | Expand executable cross-tenant and branch-isolation integration tests beyond source contracts | High | Open |
| Authentication | Add automated browser coverage for refresh rotation, CSRF, logout-all and session revocation | High | Open |
| Administration | Managed-user create/update now enforces tenant roles/branches, strong passwords, auditing and deactivation session revocation | High | Improved |
| RBAC | Add executable privilege-escalation tests for role assignment and permission changes | High | Open |
| Organization | Expand audit-log coverage verification across remaining low-risk CRUD endpoints | Medium | Open |
| Admission | Add end-to-end CRM conversion regression tests | Medium | Open |
