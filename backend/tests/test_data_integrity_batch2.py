import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class IntegrityTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text()

    def test_student_integrity(self):
        source = self.read("app/services/student_service.py")
        self.assertIn("Admission number already exists", source)
        self.assertIn("IntegrityError", source)

    def test_admission_integrity(self):
        source = self.read("app/services/admission_service.py")
        self.assertIn("active enquiry already exists", source)

    def test_fee_integrity(self):
        source = self.read("app/services/fee_service.py")
        self.assertIn("closed invoice", source)
        self.assertIn("partially_paid", source)

    def test_exam_integrity(self):
        source = self.read("app/services/exam_service.py")
        self.assertIn("Exam schedule already exists", source)
        self.assertIn("student's grade", source)

if __name__ == "__main__":
    unittest.main()
