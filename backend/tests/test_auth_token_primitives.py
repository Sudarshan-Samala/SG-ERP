import unittest
import uuid

from app.services.auth import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_matches,
)


class AuthTokenPrimitiveTests(unittest.TestCase):
    def test_refresh_tokens_are_random_and_only_digest_matches(self):
        first = generate_refresh_token()
        second = generate_refresh_token()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 48)
        digest = hash_refresh_token(first)
        self.assertNotEqual(first, digest)
        self.assertEqual(len(digest), 64)
        self.assertTrue(refresh_token_matches(first, digest))
        self.assertFalse(refresh_token_matches(second, digest))

    def test_access_token_can_be_bound_to_tenant_and_session(self):
        user_id = uuid.uuid4()
        organization_id = uuid.uuid4()
        session_id = uuid.uuid4()
        token = create_access_token(
            user_id,
            organization_id=organization_id,
            session_id=session_id,
        )
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertEqual(payload["org"], str(organization_id))
        self.assertEqual(payload["sid"], str(session_id))
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertIn("jti", payload)


if __name__ == "__main__":
    unittest.main()
