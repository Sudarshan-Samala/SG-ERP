import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RbacAssignmentContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_rbac_api_requires_manage_permission(self):
        source = self.read("app/api/rbac.py")
        self.assertGreaterEqual(source.count('require_permission("rbac.manage")'), 4)
        self.assertIn('/users/{user_id}/roles', source)

    def test_assignments_are_tenant_scoped(self):
        source = self.read("app/services/rbac_service.py")
        self.assertIn("User.organization_id == organization_id", source)
        self.assertIn("Role.organization_id == organization_id", source)
        self.assertIn("Invalid or cross-tenant role", source)

    def test_superuser_cannot_be_modified_through_tenant_role_api(self):
        source = self.read("app/services/rbac_service.py")
        self.assertIn("if user.is_superuser", source)
        self.assertIn("Superuser role assignment is not allowed", source)

    def test_rbac_permission_is_in_catalog(self):
        source = self.read("app/core/permissions.py")
        self.assertIn('"rbac.manage"', source)

if __name__ == "__main__": unittest.main()
