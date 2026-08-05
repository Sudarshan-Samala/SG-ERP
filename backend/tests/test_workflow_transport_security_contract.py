import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkflowTransportSecurityTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_communication_is_rbac_protected(self):
        source = self.read("app/api/communication.py")
        self.assertIn('require_permission("communication.read")', source)
        self.assertIn('require_permission("communication.create")', source)
        self.assertIn('require_permission("communication.manage")', source)
        self.assertIn("update_communication_status", source)

    def test_helpdesk_management_is_separate_permission(self):
        source = self.read("app/api/helpdesk.py")
        self.assertIn('require_permission("helpdesk.manage")', source)
        self.assertIn("update_ticket_status", source)

    def test_transport_handles_integrity_races(self):
        source = self.read("app/services/transport_service.py")
        self.assertIn("IntegrityError", source)
        self.assertIn("db.rollback()", source)
        self.assertIn("Route.name == route_in.name", source)
        self.assertIn("order_by(Vehicle.number)", source)

    def test_permissions_are_provisioned(self):
        source = self.read("app/core/permissions.py")
        for permission in ("communication.read", "communication.create", "communication.manage", "helpdesk.manage"):
            self.assertIn(f'"{permission}"', source)
        self.assertIn('"Communication Manager"', source)
        self.assertIn('"Helpdesk Manager"', source)

if __name__ == "__main__": unittest.main()
