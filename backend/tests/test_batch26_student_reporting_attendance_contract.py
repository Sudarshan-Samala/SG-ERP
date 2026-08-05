from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def s(p):return (ROOT/p).read_text()
def test_student_360_is_branch_and_permission_scoped():
 t=s('app/api/students.py');assert '@router.get("/{student_id}/profile")' in t;assert 'enforce_branch_access(current_user, student.branch_id)' in t;assert '"attendance.read" in permissions' in t;assert '"fees.read" in permissions' in t;assert '"exams.read" in permissions' in t
def test_student_mutations_enforce_branch_access():
 t=s('app/api/students.py');assert 'enforce_branch_access(current_user, student_in.branch_id)' in t;assert 'enforce_branch_access(current_user, existing.branch_id)' in t
def test_attendance_reads_and_marks_are_branch_safe():
 t=s('app/api/attendance.py');assert 'accessible_branch_ids(current_user)' in t;assert 'enforce_branch_access(current_user, branch_id)' in t;assert 'row.branch_id in allowed' in t
def test_reporting_requires_permission_and_branch_scope():
 t=s('app/api/reports.py');assert "require_permission('reports.read')" in t;assert 'accessible_branch_ids(current_user)' in t;assert 'Student.branch_id.in_(branches)' in t
def test_frontend_has_student360_and_reports():
 assert "api.get(`/students/${id}/profile`)" in s('../frontend/src/app/students/[id]/page.tsx');assert "api.get('/reports/overview')" in s('../frontend/src/app/reports/page.tsx');assert "permission:'reports.read'" in s('../frontend/src/app/layout.tsx')
