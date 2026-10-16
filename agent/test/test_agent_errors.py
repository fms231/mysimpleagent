import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from mysimpleagent.agent.agent import Agent
from mysimpleagent.context.context import Context
from mysimpleagent.tools.tool_repository import ToolRepository


class AgentToolErrorTest(unittest.TestCase):
    def test_tool_errors_are_added_to_context(self):
        calls = [
            SimpleNamespace(
                id="bad-json",
                function=SimpleNamespace(name="add", arguments="not-json"),
            ),
            SimpleNamespace(
                id="unknown-tool",
                function=SimpleNamespace(name="missing", arguments="{}"),
            ),
        ]
        first_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=calls))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [first_response, final_response]
        context = Context()

        result = Agent(llm, ToolRepository()).run("try tools", context)

        self.assertIs(result, final_response)
        tool_messages = [message for message in context.messages if message["role"] == "tool"]
        self.assertEqual(len(tool_messages), 2)
        self.assertEqual(tool_messages[0]["tool_call_id"], "bad-json")
        self.assertIn("Tool error:", tool_messages[0]["content"])
        self.assertEqual(tool_messages[1]["tool_call_id"], "unknown-tool")
        self.assertIn("Tool 'missing' not found.", tool_messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
