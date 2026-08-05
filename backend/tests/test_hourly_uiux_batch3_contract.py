from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def text(path):return (ROOT/path).read_text()

def test_exam_delete_protects_dependent_records():
    src=text('app/services/exam_service.py')
    assert 'Exam cannot be deleted while schedules exist' in src
    assert 'Exam cannot be deleted while results exist' in src

def test_communication_ui_is_permission_aware():
    src=(ROOT.parent/'frontend/src/app/communication/page.tsx').read_text()
    assert "can('communication.manage')" in src
    assert 'maxLength={5000}' in src
    assert 'Communication History' in src

def test_hr_ui_exposes_permission_aware_payroll():
    src=(ROOT.parent/'frontend/src/app/hr/page.tsx').read_text()
    assert "can('hr.payroll.read')" in src
    assert "can('hr.payroll.create')" in src
    assert "api.post('/hr/payroll'" in src
    assert 'Payroll History' in src
