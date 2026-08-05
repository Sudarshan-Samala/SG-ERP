import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class CoreSchoolRbacTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()
    def test_students(self):
        s=self.read("app/api/students.py"); self.assertIn('require_permission("students.read")',s); self.assertIn('require_permission("students.create")',s); self.assertIn('require_permission("students.manage")',s)
    def test_admissions(self):
        s=self.read("app/api/admissions.py"); self.assertIn('require_permission("admissions.read")',s); self.assertIn('require_permission("admissions.manage")',s)
    def test_attendance(self):
        s=self.read("app/api/attendance.py"); self.assertIn('require_permission("attendance.read")',s); self.assertIn('require_permission("attendance.mark")',s); self.assertIn('min(max(limit, 1), 500)',s)
    def test_catalog_and_roles(self):
        s=self.read("app/core/permissions.py"); self.assertIn('"Admissions Officer"',s); self.assertIn('"Teacher"',s); self.assertIn('"Student Records Manager"',s)

if __name__ == "__main__": unittest.main()
