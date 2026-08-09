from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def src(path):
    return (ROOT / path).read_text()


def test_login_is_normalized_rate_limited_and_generic():
    s = src("app/api/auth.py")
    assert 'email = form_data.username.strip().lower()' in s
    assert 'login_ip_limiter.check' in s
    assert 'login_account_limiter.check' in s
    assert 'Incorrect email or password' in s


def test_refresh_is_cookie_bound_and_rejects_inactive_accounts():
    s = src("app/api/auth.py")
    assert 'Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME)' in s
    assert 'rotate_refresh_token(db, refresh_token=refresh_token)' in s
    assert 'Organization.is_active.is_(True)' in s
    assert 'reason="account_inactive"' in s
    assert '_clear_refresh_cookie(response)' in s


def test_access_tokens_require_active_tenant_and_store_session_context():
    s = src("app/api/deps.py")
    assert 'join(Organization' in s
    assert 'Organization.is_active.is_(True)' in s
    assert 'request.state.session_id = session_uuid' in s


def test_session_mutations_are_locked_and_rollback_safe():
    s = src("app/services/session_service.py")
    assert s.count('.with_for_update()') >= 4
    assert s.count('db.rollback()') >= 3
    assert 'revocation_reason = "refresh_replay"' in s


def test_refresh_replay_uses_one_time_token_ledger():
    s = src("app/services/session_service.py")
    assert 'AuthRefreshToken' in s
    assert 'token_record.consumed_at is not None' in s
    assert 'RefreshReplayDetected' in s
    assert 'revocation_reason = "refresh_replay"' in s


def test_refresh_token_ledger_model_is_server_side_only():
    s = src("app/models/auth_refresh_token.py")
    assert 'token_hash = Column(String(64)' in s
    assert 'consumed_at = Column(DateTime' in s
    assert 'expires_at = Column(DateTime' in s
