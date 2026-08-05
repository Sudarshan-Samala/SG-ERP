import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ApiRbacBatch2Tests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_inventory_assets_permissions(self):
        source = self.read("app/api/inventory_assets.py")
        self.assertIn('require_permission("inventory.read")', source)
        self.assertIn('require_permission("inventory.manage")', source)
        self.assertIn('require_permission("assets.read")', source)
        self.assertIn('require_permission("assets.manage")', source)

    def test_transport_permissions(self):
        source = self.read("app/api/transport.py")
        self.assertIn('require_permission("transport.read")', source)
        self.assertIn('require_permission("transport.manage")', source)

    def test_helpdesk_permissions(self):
        source = self.read("app/api/helpdesk.py")
        self.assertIn('require_permission("helpdesk.read")', source)
        self.assertIn('require_permission("helpdesk.ticket.create")', source)
        self.assertIn("current_user.organization_id", source)

if __name__ == "__main__": unittest.main()
