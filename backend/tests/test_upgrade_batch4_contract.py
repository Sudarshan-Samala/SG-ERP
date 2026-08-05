from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(path): return (ROOT / path).read_text()
def test_finance_rbac():
    text=read('app/api/finance.py')
    assert 'finance.read' in text and 'finance.manage' in text
def test_exam_guards():
    text=read('app/services/exam_service.py')
    assert 'Maximum marks must be greater than zero' in text
    assert 'Marks obtained cannot be negative' in text
def test_asset_lifecycle():
    text=read('app/services/inventory_assets_service.py')
    assert 'Invalid asset status transition' in text
    assert 'strip().upper()' in text
