from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def frontend(path: str) -> str:
    return (ROOT / "frontend" / "src" / "app" / path / "page.tsx").read_text()


def test_attendance_ui_uses_bulk_and_exception_endpoints():
    source = frontend("attendance")
    assert "/attendance/exceptions" in source
    assert "/attendance/bulk" in source
    assert "can('attendance.mark')" in source
    assert "All accessible branches" in source


def test_exams_ui_uses_branch_secured_result_analytics():
    source = frontend("exams")
    assert "/exams/results/summary" in source
    assert "can('exam.result.read')" in source
    assert "can('exam.result.create')" in source
    assert "Result analytics" in source


def test_finance_ui_uses_server_reconciliation_and_export():
    source = frontend("finance")
    assert "/finance/reconciliation" in source
    assert "/finance/journal/export" in source
    assert "responseType:'blob'" in source
    assert "can('finance.manage')" in source
