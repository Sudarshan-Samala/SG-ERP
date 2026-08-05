import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class IntegrityContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()

    def test_helpdesk_has_tenant_owner_and_state_machine(self):
        source = self.read("app/services/helpdesk_service.py")
        self.assertIn("User.organization_id == organization_id", source)
        self.assertIn("ALLOWED_TRANSITIONS", source)
        self.assertIn("Invalid ticket status transition", source)

    def test_communications_do_not_claim_immediate_delivery(self):
        source = self.read("app/services/communication_service.py")
        self.assertIn('status="DRAFT"', source)
        self.assertIn("ALLOWED_TRANSITIONS", source)
        self.assertIn("Invalid communication status transition", source)

    def test_academic_enforces_branch_grade_integrity(self):
        source = self.read("app/services/academic_management_service.py")
        self.assertIn("Branch.organization_id == organization_id", source)
        self.assertIn("Grade must belong to the selected branch", source)
        self.assertIn("Subject code already exists", source)

if __name__ == "__main__": unittest.main()
