import unittest
from unittest.mock import MagicMock, patch

from app.services.bootstrap import bootstrap_super_admin


class BootstrapSuperAdminTests(unittest.TestCase):
    def _query(self, db, user_super_admin=None, user_email=None, organization=None):
        user_query = MagicMock()
        super_filter = MagicMock()
        email_filter = MagicMock()
        super_filter.first.return_value = user_super_admin
        email_filter.first.return_value = user_email
        user_query.filter.side_effect = [super_filter, email_filter]

        org_query = MagicMock()
        org_ordered = MagicMock()
        org_ordered.first.return_value = organization
        org_query.order_by.return_value = org_ordered
        db.query.side_effect = [user_query, user_query, org_query]

    def test_existing_super_admin_is_idempotent_noop(self):
        db = MagicMock()
        user_query = MagicMock()
        filtered = MagicMock()
        filtered.first.return_value = object()
        user_query.filter.return_value = filtered
        db.query.return_value = user_query

        with patch("app.services.bootstrap.get_password_hash") as hasher:
            result = bootstrap_super_admin(db, "admin@example.com", "secret")

        self.assertFalse(result.created)
        self.assertEqual(result.reason, "super_admin_exists")
        hasher.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_existing_email_is_not_overwritten_or_promoted(self):
        db = MagicMock()
        self._query(db, user_super_admin=None, user_email=object())

        with patch("app.services.bootstrap.get_password_hash") as hasher:
            result = bootstrap_super_admin(db, "admin@example.com", "secret")

        self.assertFalse(result.created)
        self.assertEqual(result.reason, "email_already_exists")
        hasher.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_creates_super_admin_with_existing_hash_utility(self):
        db = MagicMock()
        organization = MagicMock()
        organization.id = "org-id"
        self._query(db, organization=organization)

        def refresh(user):
            user.id = "user-id"

        db.refresh.side_effect = refresh
        with patch("app.services.bootstrap.get_password_hash", return_value="hashed-value") as hasher:
            result = bootstrap_super_admin(db, " Admin@Example.com ", "secret")

        self.assertTrue(result.created)
        hasher.assert_called_once_with("secret")
        created_user = db.add.call_args.args[0]
        self.assertEqual(created_user.email, "admin@example.com")
        self.assertEqual(created_user.hashed_password, "hashed-value")
        self.assertTrue(created_user.is_superuser)
        self.assertTrue(created_user.is_active)
        db.commit.assert_called_once()

    def test_creates_system_organization_when_database_has_none(self):
        db = MagicMock()
        self._query(db, organization=None)

        def flush():
            organization = db.add.call_args_list[0].args[0]
            organization.id = "new-org-id"

        db.flush.side_effect = flush
        db.refresh.side_effect = lambda user: setattr(user, "id", "user-id")

        with patch("app.services.bootstrap.get_password_hash", return_value="hashed-value"):
            result = bootstrap_super_admin(db, "admin@example.com", "secret")

        self.assertTrue(result.created)
        self.assertEqual(db.add.call_count, 2)
        db.flush.assert_called_once()
        db.commit.assert_called_once()

    def test_missing_credentials_fail_before_hashing(self):
        db = MagicMock()
        with patch("app.services.bootstrap.get_password_hash") as hasher:
            with self.assertRaises(ValueError):
                bootstrap_super_admin(db, "", "secret")
            with self.assertRaises(ValueError):
                bootstrap_super_admin(db, "admin@example.com", "")
        hasher.assert_not_called()
        db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
