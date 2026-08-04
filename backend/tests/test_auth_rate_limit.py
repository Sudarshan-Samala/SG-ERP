import unittest

from fastapi import HTTPException

from app.services.rate_limit import SlidingWindowRateLimiter


class AuthRateLimitTests(unittest.TestCase):
    def test_limit_returns_429_and_retry_after(self):
        limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
        limiter.check("login:127.0.0.1", now=100.0)
        limiter.check("login:127.0.0.1", now=101.0)
        with self.assertRaises(HTTPException) as raised:
            limiter.check("login:127.0.0.1", now=102.0)
        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("Retry-After", raised.exception.headers)

    def test_window_expiry_allows_new_request(self):
        limiter = SlidingWindowRateLimiter(limit=1, window_seconds=10)
        limiter.check("refresh:127.0.0.1", now=100.0)
        limiter.check("refresh:127.0.0.1", now=111.0)

    def test_keys_are_isolated(self):
        limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
        limiter.check("login:10.0.0.1", now=100.0)
        limiter.check("login:10.0.0.2", now=100.0)


if __name__ == "__main__":
    unittest.main()
