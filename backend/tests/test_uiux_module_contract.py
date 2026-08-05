from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def frontend(path: str) -> str:
    return (ROOT / "frontend" / "src" / "app" / path / "page.tsx").read_text()


def test_students_ui_is_permission_aware():
    text = frontend("students")
    assert "can('students.create')" in text
    assert "can('students.manage')" in text
    assert "apiErrorMessage" in text


def test_exams_ui_validates_dates_and_permissions():
    text = frontend("exams")
    assert "can('exam.manage')" in text
    assert "End date cannot be before start date" in text
    assert "min={form.start_date||undefined}" in text


def test_fees_ui_validates_positive_amount_and_permissions():
    text = frontend("fees")
    assert "can('fees.invoice.create')" in text
    assert "amount<=0" in text
    assert "Total Invoiced" in text
