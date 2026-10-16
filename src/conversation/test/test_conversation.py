import unittest
from unittest.mock import Mock

from src.context.context import Context
from src.conversation.conversation import Conversation


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


if __name__ == "__main__":
    unittest.main()
