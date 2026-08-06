from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def src(path:str)->str:
    return (ROOT/path).read_text()

def test_reconciliation_drilldown_is_tenant_and_permission_scoped():
    api=src('app/api/finance.py')
    assert "@router.get('/reconciliation/drilldown')" in api
    assert "require_permission('finance.read')" in api
    assert "get_accounts(db,current_org.id)" in api
    assert "get_journal_entries(db,current_org.id" in api

def test_drilldown_reports_account_level_debit_credit_differences():
    api=src('app/api/finance.py')
    assert "'total_debit':debit" in api
    assert "'total_credit':credit" in api
    assert "'difference':difference" in api
    assert "-abs(item['difference'])" in api

def test_frontend_consumes_authoritative_drilldown_endpoint():
    page=src('../frontend/src/app/finance/page.tsx')
    assert "api.get('/finance/reconciliation/drilldown'" in page
    assert 'Reconciliation Drill-down' in page
    assert 'row.total_debit' in page
    assert 'row.total_credit' in page
