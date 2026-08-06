import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Batch46HardeningContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text()

    def test_attendance_bulk_uses_typed_records_and_hides_unknown_students(self):
        source = self.read('app/api/attendance.py')
        self.assertIn('class BulkAttendanceRecord(BaseModel):', source)
        self.assertIn("Literal['PRESENT', 'ABSENT', 'LATE']", source)
        self.assertIn('if not student:', source)
        self.assertIn('return query.filter(False)', source)

    def test_exam_conflicts_use_explicit_http_409_constant(self):
        source = self.read('app/services/exam_service.py')
        self.assertIn('HTTP_409_CONFLICT', source)
        self.assertIn('Exam result already exists', source)
        self.assertIn('Exam cannot be deleted while results exist', source)

    def test_fee_mutations_commit_with_audit_atomically(self):
        source = self.read('app/services/fee_service.py')
        self.assertIn('def _commit_audited', source)
        self.assertIn("'CREATE', 'PAYMENT'", source)
        self.assertIn("'CREATE', 'INVOICE'", source)
        self.assertIn('Invoice has no outstanding balance', source)
        self.assertIn('Fee structure amount must be greater than zero', source)


if __name__ == '__main__':
    unittest.main()
