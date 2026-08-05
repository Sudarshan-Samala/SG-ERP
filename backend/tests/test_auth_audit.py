import unittest

from app.models.auth_security_event import AuthSecurityEvent
from app.services.auth_audit import email_fingerprint


class AuthAuditTests(unittest.TestCase):
    def test_security_event_never_has_secret_or_raw_email_columns(self):
        columns = set(AuthSecurityEvent.__table__.columns.keys())
        self.assertNotIn("password", columns)
        self.assertNotIn("access_token", columns)
        self.assertNotIn("refresh_token", columns)
        self.assertNotIn("email", columns)
        self.assertIn("email_fingerprint", columns)

    def test_email_fingerprint_is_normalized_and_not_plaintext(self):
        first = email_fingerprint(" Admin@Example.COM ")
        second = email_fingerprint("admin@example.com")
        self.assertEqual(first, second)
        self.assertNotEqual(first, "admin@example.com")
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()
