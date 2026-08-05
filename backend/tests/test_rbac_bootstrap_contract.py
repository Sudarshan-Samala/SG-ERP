import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RbacBootstrapContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_catalog_contains_protected_api_permissions(self):
        source = self.read("app/core/permissions.py")
        for name in ("fees.payment.collect", "hr.payroll.create", "exam.result.create", "inventory.manage", "assets.manage", "transport.manage", "helpdesk.ticket.create"):
            self.assertIn(f'"{name}"', source)

    def test_bootstrap_is_tenant_scoped_and_idempotent(self):
        source = self.read("app/services/rbac_bootstrap.py")
        self.assertIn("Role.organization_id == organization.id", source)
        self.assertIn("Permission(name=name", source)
        self.assertIn("role.permissions =", source)

    def test_deploy_bootstrap_runs_rbac_sync(self):
        source = self.read("app/scripts/bootstrap_admin.py")
        self.assertIn("bootstrap_rbac(db)", source)
        self.assertNotIn("password}", source)

if __name__ == "__main__": unittest.main()
