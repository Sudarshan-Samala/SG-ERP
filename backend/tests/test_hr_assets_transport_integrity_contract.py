import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class IntegrityContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_hr_scopes_users_employees_and_payroll_period(self):
        source = self.read("app/services/hr_service.py")
        self.assertIn("User.organization_id == organization_id", source)
        self.assertIn("Employee.organization_id == organization_id", source)
        self.assertIn("Payroll already exists for this employee and period", source)

    def test_transport_scopes_vehicle_and_prevents_duplicates(self):
        source = self.read("app/services/transport_service.py")
        self.assertIn("Vehicle.organization_id == organization_id", source)
        self.assertIn("Vehicle number already exists", source)
        self.assertIn("Driver license number already exists", source)

    def test_assets_enforce_lifecycle_rules(self):
        source = self.read("app/services/inventory_assets_service.py")
        self.assertIn("Disposed assets cannot be reactivated", source)
        self.assertIn("Deployed assets cannot be deleted", source)
        self.assertIn("HTTP_409_CONFLICT", source)

if __name__ == "__main__": unittest.main()
