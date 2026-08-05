import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IntegrityContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text()

    def test_admissions_scope_branch_and_academic_year(self):
        source = self.read("app/services/admission_service.py")
        self.assertIn("Branch.organization_id == organization_id", source)
        self.assertIn("AcademicYear.organization_id == organization_id", source)

    def test_exams_scope_referenced_entities(self):
        source = self.read("app/services/exam_service.py")
        self.assertIn("_require_owned(db, ExamType", source)
        self.assertIn("_require_owned(db, Student", source)
        self.assertIn("Exam schedule date must fall within the exam date range", source)
        self.assertIn("HTTP_409_CONFLICT", source)

    def test_finance_scopes_journal_account(self):
        source = self.read("app/services/finance_service.py")
        self.assertIn("Account.organization_id == organization_id", source)
        self.assertIn("Account does not belong to this organization", source)


if __name__ == "__main__":
    unittest.main()
