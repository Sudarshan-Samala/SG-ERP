from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_signup_security_contract():
 t=src('app/api/signup.py');assert "@router.post('/signup'" in t;assert 'AUTH_SIGNUP_RATE_LIMIT' in t;assert 'get_password_hash(payload.password)' in t;assert "func.lower(Organization.name)" in t;assert 'db.query(Permission).all()' in t;assert "record_auth_event(db, event_type='signup'" in t
def test_signup_is_registered_under_auth():
 t=src('app/main.py');assert "from app.api.signup import router as signup_router" in t;assert "app.include_router(signup_router,prefix='/api/v1/auth'" in t
def test_frontend_signup_flow():
 t=src('../frontend/src/app/login/page.tsx');assert "mode==='signup'" in t;assert "api.post('/auth/signup'" in t;assert "localStorage.setItem('session_id'" in t;assert 'password!==confirm' in t
