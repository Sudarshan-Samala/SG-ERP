from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT.parent / "frontend" / "src" / "app"


def backend(path: str) -> str:
    return (ROOT / path).read_text()


def frontend(path: str) -> str:
    return (FRONTEND / path).read_text()


def test_finance_workspace_uses_rbac_and_current_journal_contract():
    text = frontend("finance/page.tsx")
    assert "finance.manage" in text
    assert "/finance/accounts" in text
    assert "/finance/journal" in text
    assert "amount,type:entry.type,date:new Date().toISOString()" in text
    assert "Total Debit" in text and "Total Credit" in text


def test_hr_workspace_manages_salary_structures_before_payroll():
    text = frontend("hr/page.tsx")
    assert "hr.salary.manage" in text
    assert "/hr/salary-structures" in text
    assert "Configure Salary Structure" in text
    assert "employees.filter(e=>salaries.some" in text


def test_exam_backend_retains_branch_isolation_and_schedule_permissions():
    text = backend("app/api/exams.py")
    assert 'require_permission("exam.schedule.manage")' in text
    assert 'require_permission("exam.result.create")' in text
    assert "accessible_branch_ids(current_user)" in text
    assert "enforce_branch_access(current_user, student.branch_id)" in text
