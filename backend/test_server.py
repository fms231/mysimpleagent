import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from backend.server import get_session, get_session_lock, model_context_limit
from mysimpleagent.conversation.conversation import Conversation


class SessionLockTest(unittest.TestCase):
    @patch("backend.server.get_model_metadata")
    def test_model_context_limit_includes_input_and_output_tokens(self, get_metadata):
        get_metadata.return_value = {
            "max_input_tokens": 922000,
            "max_output_tokens": 128000,
        }

        self.assertEqual(model_context_limit("gpt-6-luna"), 1050000)

    @patch("backend.server.get_model_metadata", return_value={
        "max_input_tokens": 900,
        "max_output_tokens": 100,
        "max_context_window": 800,
    })
    def test_model_context_limit_prefers_context_window(self, _get_metadata):
        self.assertEqual(model_context_limit("custom/model"), 800)

    @patch("backend.server.get_model_metadata", return_value={"max_input_tokens": 900})
    def test_model_context_limit_falls_back_to_input_limit(self, _get_metadata):
        self.assertEqual(model_context_limit("custom/model"), 900)

    def test_requests_for_same_session_share_lock(self):
        self.assertIs(get_session_lock("session-1"), get_session_lock("session-1"))

    def test_different_sessions_have_different_locks(self):
        self.assertIsNot(get_session_lock("session-a"), get_session_lock("session-b"))


    def test_get_checks_session_file_after_acquiring_lock(self):
        acquired = threading.Event()
        release = threading.Event()
        result = {}

        class WaitingLock:
            def __enter__(self):
                acquired.set()
                release.wait(timeout=2)

            def __exit__(self, *_):
                return False

        with tempfile.TemporaryDirectory() as directory:
            sessions_dir = Path(directory)
            session_file = sessions_dir / "session-1.jsonl"

            def call_get_session():
                try:
                    result["response"] = get_session("session-1")
                except Exception as error:
                    result["error"] = error

            with patch("backend.server.SESSIONS_DIR", sessions_dir), patch(
                "backend.server.get_session_lock", return_value=WaitingLock()
            ), patch(
                "backend.server.Conversation",
                side_effect=lambda agent, session_id: Conversation(
                    agent, session_id=session_id, sessions_dir=str(sessions_dir)
                ),
            ):
                thread = threading.Thread(target=call_get_session)
                thread.start()
                self.assertTrue(acquired.wait(timeout=1))
                session_file.write_text(
                    json.dumps({"id": 0, "role": "user", "content": "hello"}) + "\n",
                    encoding="utf-8",
                )
                release.set()
                thread.join(timeout=2)

            self.assertFalse(thread.is_alive())
            self.assertNotIn("error", result)
            self.assertEqual(result["response"]["messages"][0]["content"], "hello")


if __name__ == "__main__":
    unittest.main()
