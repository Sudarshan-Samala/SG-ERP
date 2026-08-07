import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HourlyBatchTests(unittest.TestCase):
    def test_reporting_date_window_is_half_open(self):
        from app.api.reports import _date_window

        start, end = _date_window(date(2026, 8, 1), date(2026, 8, 7))
        self.assertEqual(start, datetime(2026, 8, 1))
        self.assertEqual(end, datetime(2026, 8, 8))

    def test_reporting_rejects_reversed_date_window(self):
        from fastapi import HTTPException
        from app.api.reports import _date_window

        with self.assertRaises(HTTPException) as ctx:
            _date_window(date(2026, 8, 8), date(2026, 8, 1))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_admission_pipeline_transitions_remain_fail_closed(self):
        from app.services.admission_service import ADMISSION_TRANSITIONS

        self.assertNotIn('SELECTED', ADMISSION_TRANSITIONS['ENQUIRY'])
        self.assertIn('SELECTED', ADMISSION_TRANSITIONS['APPLIED'])
        self.assertEqual(ADMISSION_TRANSITIONS['ADMITTED'], set())
        self.assertEqual(ADMISSION_TRANSITIONS['CLOSED'], set())

    def test_attendance_correction_workflow_has_distinct_permissions_and_model(self):
        permissions = (ROOT / 'app/core/permissions.py').read_text()
        model = (ROOT / 'app/models/workflow_extensions.py').read_text()
        api = (ROOT / 'app/api/attendance.py').read_text()
        self.assertIn('attendance.correction.request', permissions)
        self.assertIn('attendance.correction.approve', permissions)
        self.assertIn('class AttendanceCorrection(Base):', model)
        self.assertIn("status=Column(String,nullable=False,default='PENDING'", model)
        self.assertIn("@router.patch('/corrections/{correction_id}')", api)
        self.assertIn("require_permission('attendance.correction.approve')", api)
        self.assertIn("status == 'PENDING'", api)


if __name__ == '__main__':
    unittest.main()
