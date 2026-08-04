import unittest

from app.api import auth


class AuthApiContractTests(unittest.TestCase):
    def test_required_session_endpoints_are_registered(self):
        paths = {route.path for route in auth.router.routes}
        self.assertIn("/login", paths)
        self.assertIn("/refresh", paths)
        self.assertIn("/logout", paths)
        self.assertIn("/logout-all", paths)
        self.assertIn("/me", paths)

    def test_refresh_request_does_not_accept_refresh_credential_in_body(self):
        schema = auth.RefreshRequest.model_json_schema()
        self.assertEqual(set(schema["required"]), {"session_id", "organization_id"})
        self.assertNotIn("refresh_token", schema.get("properties", {}))

    def test_login_response_never_exposes_refresh_credential(self):
        schema = auth.SessionToken.model_json_schema()
        properties = schema.get("properties", {})
        self.assertTrue({"access_token", "token_type", "session_id"}.issubset(set(schema["required"])))
        self.assertNotIn("refresh_token", properties)

    def test_refresh_cookie_is_httponly_secure_and_scoped(self):
        class FakeResponse:
            def __init__(self):
                self.kwargs = None

            def set_cookie(self, **kwargs):
                self.kwargs = kwargs

        response = FakeResponse()
        auth._set_refresh_cookie(response, "test-secret")
        self.assertTrue(response.kwargs["httponly"])
        self.assertTrue(response.kwargs["secure"])
        self.assertEqual(response.kwargs["path"], "/api/v1/auth")
        self.assertNotEqual(response.kwargs["samesite"], "none")


if __name__ == "__main__":
    unittest.main()
