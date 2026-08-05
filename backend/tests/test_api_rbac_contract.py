import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ApiRbacContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_permission_dependency_is_default_deny(self):
        source = self.read("app/api/deps.py")
        self.assertIn("def require_permission", source)
        self.assertIn("HTTP_403_FORBIDDEN", source)
        self.assertIn("permission_name not in permissions", source)

    def test_fees_use_granular_permissions(self):
        source = self.read("app/api/fees.py")
        self.assertIn('require_permission("fees.read")', source)
        self.assertIn('require_permission("fees.payment.collect")', source)

    def test_hr_uses_granular_permissions(self):
        source = self.read("app/api/hr.py")
        self.assertIn('require_permission("hr.employee.read")', source)
        self.assertIn('require_permission("hr.payroll.create")', source)

    def test_exams_use_granular_permissions(self):
        source = self.read("app/api/exams.py")
        self.assertIn('require_permission("exam.read")', source)
        self.assertIn('require_permission("exam.result.create")', source)

if __name__ == "__main__": unittest.main()
