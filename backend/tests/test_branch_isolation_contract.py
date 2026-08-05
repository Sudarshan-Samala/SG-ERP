import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class BranchIsolationContractTests(unittest.TestCase):
    def read(self, path): return (ROOT / path).read_text()
    def test_branch_helper_default_denies(self):
        s=self.read('app/api/deps.py'); self.assertIn('def enforce_branch_access',s); self.assertIn('Branch access denied',s)
    def test_users_are_rbac_and_tenant_scoped(self):
        api=self.read('app/api/users.py'); svc=self.read('app/services/user_management_service.py'); self.assertIn('users.manage',api); self.assertIn('Branch.organization_id == user_in.organization_id',svc); self.assertIn('Role.organization_id == user_in.organization_id',svc)
    def test_branch_admin_is_protected(self):
        s=self.read('app/api/branches.py'); self.assertIn('branches.read',s); self.assertIn('branches.manage',s)
    def test_students_enforce_branch_access(self):
        s=self.read('app/api/students.py'); self.assertIn('enforce_branch_access(current_user, student_in.branch_id)',s); self.assertIn('accessible_branch_ids(current_user)',s)
    def test_attendance_enforces_branch_access(self):
        s=self.read('app/api/attendance.py'); self.assertIn('enforce_branch_access(current_user, att_in.branch_id)',s); self.assertIn('accessible_branch_ids(current_user)',s)
if __name__ == '__main__': unittest.main()
