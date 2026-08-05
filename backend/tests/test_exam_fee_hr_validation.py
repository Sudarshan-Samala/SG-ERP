import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.exam import ExamCreate, ExamScheduleCreate
from app.schemas.fee import FeeStructureCreate, PaymentCreate
from app.schemas.hr import PayrollCreate, SalaryStructureCreate


class ExamFeeHrValidationTests(unittest.TestCase):
    def test_exam_rejects_reversed_dates(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValidationError):
            ExamCreate(exam_type_id=uuid4(), name="Term Exam", start_date=now, end_date=now - timedelta(days=1))

    def test_exam_schedule_requires_positive_max_marks(self):
        with self.assertRaises(ValidationError):
            ExamScheduleCreate(exam_id=uuid4(), subject_id=uuid4(), grade_id=uuid4(), date=datetime.now(timezone.utc), max_marks=0)

    def test_fee_structure_rejects_zero_amount(self):
        with self.assertRaises(ValidationError):
            FeeStructureCreate(grade_id=uuid4(), fee_type_id=uuid4(), amount=0)

    def test_payment_rejects_unknown_method(self):
        with self.assertRaises(ValidationError):
            PaymentCreate(invoice_id=uuid4(), amount_paid=100, payment_date=datetime.now(timezone.utc), payment_method="crypto")

    def test_salary_rejects_negative_amounts(self):
        with self.assertRaises(ValidationError):
            SalaryStructureCreate(employee_id=uuid4(), basic_salary=-1, hra=0)

    def test_payroll_rejects_invalid_month(self):
        with self.assertRaises(ValidationError):
            PayrollCreate(employee_id=uuid4(), month=13, year=2026, net_salary=1000)


if __name__ == "__main__":
    unittest.main()
