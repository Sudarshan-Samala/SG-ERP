import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.admission import AdmissionEnquiryCreate
from app.schemas.attendance import AttendanceCreate
from app.schemas.student import StudentCreate


class CoreModuleValidationTests(unittest.TestCase):
    def test_student_rejects_future_birth_date(self):
        with self.assertRaises(ValidationError):
            StudentCreate(branch_id=uuid4(), academic_year_id=uuid4(), admission_number="A-1", student_name="Student One", date_of_birth=datetime.now(timezone.utc) + timedelta(days=1), gender="male")

    def test_student_rejects_unknown_gender(self):
        with self.assertRaises(ValidationError):
            StudentCreate(branch_id=uuid4(), academic_year_id=uuid4(), admission_number="A-1", student_name="Student One", date_of_birth=datetime(2015, 1, 1, tzinfo=timezone.utc), gender="unknown")

    def test_admission_rejects_blank_names(self):
        with self.assertRaises(ValidationError):
            AdmissionEnquiryCreate(branch_id=uuid4(), academic_year_id=uuid4(), student_name="  ", parent_name="Parent", email="parent@example.com", phone="9876543210")

    def test_attendance_rejects_invalid_status(self):
        with self.assertRaises(ValidationError):
            AttendanceCreate(branch_id=uuid4(), student_id=uuid4(), date=datetime.now(timezone.utc), status="holiday")

    def test_attendance_accepts_supported_status(self):
        attendance = AttendanceCreate(branch_id=uuid4(), student_id=uuid4(), date=datetime.now(timezone.utc), status="present")
        self.assertEqual(attendance.status, "present")


if __name__ == "__main__":
    unittest.main()
