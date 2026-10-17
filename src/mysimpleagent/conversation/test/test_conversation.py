import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from mysimpleagent.context.context import Context
from mysimpleagent.conversation.conversation import Conversation


class ConversationTest(unittest.TestCase):
    def test_send_strategy_failure_restores_context(self):
        class RejectMessage:
            def check(self, context):
                raise ValueError("message rejected")

        context = Context(context_strategy=RejectMessage())
        context.messages = [{"id": 4, "role": "user", "content": "existing"}]
        context.id = 5
        conversation = Conversation(Mock(), context)

        with self.assertRaisesRegex(ValueError, "message rejected"):
            conversation.send("new")

        self.assertEqual(context.messages, [{"id": 4, "role": "user", "content": "existing"}])
        self.assertEqual(context.id, 5)

    def test_edit_strategy_failure_restores_context(self):
        class RejectMessage:
            def check(self, context):
                raise ValueError("message rejected")

        context = Context()
        context.add_message("user", "first")
        context.add_message("assistant", "answer")
        context.context_strategy = RejectMessage()
        original_messages = [message.copy() for message in context.messages]
        original_id = context.id
        conversation = Conversation(Mock(), context)

        with self.assertRaisesRegex(ValueError, "message rejected"):
            conversation.edit_and_send(0, "edited")

        self.assertEqual(context.messages, original_messages)
        self.assertEqual(context.id, original_id)

    def test_send_uses_conversation_context(self):
        agent = Mock()
        response = object()
        agent.run.return_value = response
        context = Context()
        conversation = Conversation(agent, context)

        result = conversation.send("你好")

        self.assertIs(result, response)
        agent.run.assert_called_once_with(context)

    def test_send_persists_context_by_session_id(self):
        agent = Mock()
        agent.run.side_effect = lambda context: context.add_message("assistant", "你好")

        with TemporaryDirectory() as directory:
            conversation = Conversation(agent, sessions_dir=directory, session_id="session-1")
            conversation.send("你好")
            path = Path(directory) / "session-1.jsonl"

            self.assertTrue(path.exists())
            restored = Conversation(agent, sessions_dir=directory, session_id="session-1")

        self.assertEqual(restored.context.messages, [
            {"id": 0, "role": "user", "content": "你好"},
            {"id": 1, "role": "assistant", "content": "你好"},
        ])

    def test_send_failure_restores_context_and_does_not_persist(self):
        agent = Mock()
        context = Context()
        context.add_message("user", "existing")

        def mutate_then_fail(current_context):
            current_context.messages[0]["content"] = "mutated"
            raise RuntimeError("LLM failed")

        agent.run.side_effect = mutate_then_fail

        with TemporaryDirectory() as directory:
            conversation = Conversation(agent, context, session_id="session-1", sessions_dir=directory)
            with self.assertRaisesRegex(RuntimeError, "LLM failed"):
                conversation.send("new")

            self.assertEqual(context.messages, [{"id": 0, "role": "user", "content": "existing"}])
            self.assertFalse((Path(directory) / "session-1.jsonl").exists())

    def test_edit_failure_restores_context_and_saved_history(self):
        agent = Mock()
        context = Context()
        context.add_message("user", "a1")
        context.add_message("assistant", "b1")
        context.add_message("user", "a2")
        context.add_message("assistant", "b2")

        def mutate_then_fail(current_context):
            current_context.messages[0]["content"] = "mutated"
            raise RuntimeError("LLM failed")

        agent.run.side_effect = mutate_then_fail

        with TemporaryDirectory() as directory:
            conversation = Conversation(agent, context, session_id="session-1", sessions_dir=directory)
            conversation.context.save_to_file(str(conversation.session_file))
            original_file = conversation.session_file.read_text(encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "LLM failed"):
                conversation.edit_and_send(2, "a2-edited")

            self.assertEqual([message["content"] for message in context.messages], ["a1", "b1", "a2", "b2"])
            self.assertEqual(conversation.session_file.read_text(encoding="utf-8"), original_file)

    def test_rejects_unsafe_session_id(self):
        with self.assertRaises(ValueError):
            Conversation(Mock(), session_id="../../outside")


if __name__ == "__main__":
    unittest.main()
