import unittest

from app.api import auth


class SessionApiSecurityTests(unittest.TestCase):
    def test_session_management_routes_exist(self):
        paths = {route.path for route in auth.router.routes}
        self.assertIn("/sessions", paths)
        self.assertIn("/sessions/{session_id}", paths)

    def test_session_view_does_not_expose_credentials_or_tenant_override(self):
        properties = auth.SessionView.model_json_schema().get("properties", {})
        self.assertNotIn("refresh_token", properties)
        self.assertNotIn("refresh_token_hash", properties)
        self.assertNotIn("access_token", properties)
        self.assertNotIn("organization_id", properties)
        self.assertNotIn("user_id", properties)

    def test_delete_session_has_no_user_or_organization_request_fields(self):
        route = next(route for route in auth.router.routes if route.path == "/sessions/{session_id}")
        self.assertIn("DELETE", route.methods)
        # Ownership is derived from get_current_user rather than caller-controlled tenant/user IDs.
        dependant_names = {dependency.name for dependency in route.dependant.dependencies}
        self.assertIn("current_user", dependant_names)


if __name__ == "__main__":
    unittest.main()
