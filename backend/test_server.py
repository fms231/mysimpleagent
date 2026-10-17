import unittest

from backend.server import get_session_lock


class SessionLockTest(unittest.TestCase):
    def test_requests_for_same_session_share_lock(self):
        self.assertIs(get_session_lock("session-1"), get_session_lock("session-1"))

    def test_different_sessions_have_different_locks(self):
        self.assertIsNot(get_session_lock("session-a"), get_session_lock("session-b"))


if __name__ == "__main__":
    unittest.main()
