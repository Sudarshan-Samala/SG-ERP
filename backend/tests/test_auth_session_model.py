import unittest

from app.models.auth_session import AuthSession


class AuthSessionModelTests(unittest.TestCase):
    def test_session_contains_required_tenant_and_refresh_fields(self):
        columns = AuthSession.__table__.columns
        required = {
            "id",
            "user_id",
            "organization_id",
            "token_family_id",
            "refresh_token_hash",
            "previous_refresh_token_hash",
            "created_at",
            "last_used_at",
            "expires_at",
            "revoked_at",
            "revocation_reason",
        }
        self.assertTrue(required.issubset(set(columns.keys())))
        self.assertFalse(columns.organization_id.nullable)
        self.assertFalse(columns.user_id.nullable)
        self.assertFalse(columns.refresh_token_hash.nullable)

    def test_refresh_hash_is_unique_and_plaintext_token_column_does_not_exist(self):
        columns = AuthSession.__table__.columns
        self.assertTrue(columns.refresh_token_hash.unique)
        self.assertNotIn("refresh_token", columns.keys())
        self.assertNotIn("access_token", columns.keys())

    def test_session_has_tenant_user_family_and_expiry_indexes(self):
        index_columns = {tuple(column.name for column in index.columns) for index in AuthSession.__table__.indexes}
        self.assertIn(("user_id", "organization_id"), index_columns)
        self.assertIn(("token_family_id",), index_columns)
        self.assertIn(("expires_at",), index_columns)


if __name__ == "__main__":
    unittest.main()
