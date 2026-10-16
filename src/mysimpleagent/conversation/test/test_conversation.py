import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from mysimpleagent.context.context import Context
from mysimpleagent.conversation.conversation import Conversation


class ConversationTest(unittest.TestCase):
    def test_send_uses_conversation_context(self):
        agent = Mock()
        response = object()
        agent.run.return_value = response
        context = Context()
        conversation = Conversation(agent, context)

        result = conversation.send("你好")

        self.assertIs(result, response)
        agent.run.assert_called_once_with("你好", context)

    def test_send_persists_context_by_session_id(self):
        agent = Mock()
        agent.run.side_effect = lambda text, context: (
            context.add_message("user", text),
            context.add_message("assistant", "你好"),
        )[-1]

        with TemporaryDirectory() as directory:
            conversation = Conversation(agent, sessions_dir=directory, session_id="session-1")
            conversation.send("你好")
            path = Path(directory) / "session-1.jsonl"

            self.assertTrue(path.exists())
            restored = Conversation(agent, sessions_dir=directory, session_id="session-1")

        self.assertEqual(restored.context.messages, [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好"},
        ])


if __name__ == "__main__":
    unittest.main()
