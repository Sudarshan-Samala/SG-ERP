import unittest

from app.api import auth


class AuthApiContractTests(unittest.TestCase):
    def test_required_session_endpoints_are_registered(self):
        routes = {(route.path, tuple(sorted(route.methods or []))) for route in auth.router.routes}
        paths = {path for path, _ in routes}
        self.assertIn("/login", paths)
        self.assertIn("/refresh", paths)
        self.assertIn("/logout", paths)
        self.assertIn("/logout-all", paths)
        self.assertIn("/me", paths)

    def test_refresh_request_requires_tenant_session_and_credential(self):
        schema = auth.RefreshRequest.model_json_schema()
        self.assertEqual(
            set(schema["required"]),
            {"session_id", "organization_id", "refresh_token"},
        )

    def test_login_response_exposes_session_rotation_contract(self):
        schema = auth.SessionToken.model_json_schema()
        self.assertTrue(
            {"access_token", "token_type", "refresh_token", "session_id"}.issubset(
                set(schema["required"])
            )
        )


if __name__ == "__main__":
    unittest.main()
