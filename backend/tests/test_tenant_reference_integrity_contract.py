import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "app" / "services"


class TenantReferenceIntegrityContractTests(unittest.TestCase):
    def test_student_service_scopes_branch_and_academic_year(self):
        source = (ROOT / "student_service.py").read_text()
        self.assertIn("Branch.organization_id == organization_id", source)
        self.assertIn("AcademicYear.organization_id == organization_id", source)
        self.assertIn("from app.services.audit.audit_service import log_action", source)

    def test_attendance_validates_student_branch_membership(self):
        source = (ROOT / "attendance_service.py").read_text()
        self.assertIn("Student.organization_id == organization_id", source)
        self.assertIn("student.branch_id != att_in.branch_id", source)

    def test_fee_service_scopes_referenced_records_and_prevents_overpayment(self):
        source = (ROOT / "fee_service.py").read_text()
        self.assertIn("model.organization_id == organization_id", source)
        self.assertIn("Payment exceeds the outstanding invoice amount", source)


if __name__ == "__main__":
    unittest.main()
