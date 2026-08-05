import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.academic_management import GradeCreate, SubjectCreate
from app.schemas.communication import CommunicationCreate
from app.schemas.transport import DriverCreate, VehicleCreate


class AcademicTransportCommunicationValidationTests(unittest.TestCase):
    def test_grade_rejects_blank_name(self):
        with self.assertRaises(ValidationError):
            GradeCreate(branch_id=uuid4(), name="   ")

    def test_subject_normalizes_code(self):
        subject = SubjectCreate(name="Mathematics", code="math_01")
        self.assertEqual(subject.code, "MATH_01")

    def test_vehicle_rejects_zero_capacity(self):
        with self.assertRaises(ValidationError):
            VehicleCreate(number="KA01AB1234", capacity=0)

    def test_driver_rejects_blank_license(self):
        with self.assertRaises(ValidationError):
            DriverCreate(name="Driver One", license_number="   ")

    def test_communication_rejects_unknown_channel(self):
        with self.assertRaises(ValidationError):
            CommunicationCreate(recipient_type="ALL", channel="TELEGRAM", content="Notice")

    def test_communication_rejects_blank_content(self):
        with self.assertRaises(ValidationError):
            CommunicationCreate(recipient_type="BRANCH", channel="IN_APP", content="   ")


if __name__ == "__main__":
    unittest.main()
