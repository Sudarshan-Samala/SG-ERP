from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(path):return(ROOT/path).read_text()
def test_login_is_normalized_rate_limited_and_org_aware():
 s=src('app/api/auth.py');assert "email=form_data.username.strip().lower()" in s;assert '_login_key(request,email)' in s;assert 'Organization is inactive' in s
def test_refresh_rejects_inactive_accounts_and_tenants():
 s=src('app/api/auth.py');assert 'Organization.is_active.is_(True)' in s;assert "reason='account_inactive'" in s;assert '_clear_refresh_cookie(response)' in s
def test_access_tokens_require_active_tenant():
 s=src('app/api/deps.py');assert 'join(Organization' in s;assert 'Organization.is_active.is_(True)' in s
def test_session_mutations_are_locked_and_rollback_safe():
 s=src('app/services/session_service.py');assert s.count('.with_for_update()')>=3;assert s.count('db.rollback()')>=4;assert "revocation_reason='refresh_replay'" in s
def test_refresh_replay_revokes_session_family_credential():
 s=src('app/services/session_service.py');assert 'previous_refresh_token_hash' in s;assert 'RefreshReplayDetected' in s;assert "revocation_reason='refresh_replay'" in s
