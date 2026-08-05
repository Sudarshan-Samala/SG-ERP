import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class IntegrityTests(unittest.TestCase):
    def read(self, p): return (ROOT / p).read_text()
    def test_hr(self):
        s=self.read("app/services/hr_service.py"); self.assertIn("Employee.employee_id == emp_in.employee_id",s); self.assertIn("Payroll month must be between 1 and 12",s); self.assertIn("except IntegrityError",s)
    def test_inventory(self):
        s=self.read("app/services/inventory_assets_service.py"); self.assertIn("Inventory quantity cannot be negative",s); self.assertGreaterEqual(s.count("Asset tag already exists"),2); self.assertIn("Disposed assets cannot be reactivated",s)
    def test_attendance(self):
        s=self.read("app/services/attendance_service.py"); self.assertIn("Attendance cannot be marked for a future date",s); self.assertIn("Attendance has already been marked",s); self.assertIn("Student does not belong to the selected branch",s)

if __name__ == "__main__": unittest.main()
