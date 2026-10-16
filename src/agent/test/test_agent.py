import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.agent.agent import Agent
from src.context.context import Context
from src.tools.tool_repository import ToolRepository
from src.tools.tool_schema import ToolSchema


class AgentTest(unittest.TestCase):
    def _repository(self):
        tool = ToolSchema()
        tool.name = "add"
        tool.description = "Add two numbers."
        tool.func = lambda a, b: a + b
        tool.parameters = {"type": "object"}

        repository = ToolRepository()
        repository.add_tool(tool)
        return repository

    def test_returns_response_without_tool_calls(self):
        repository = self._repository()
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None))]
        )
        llm = Mock()
        llm.chat.return_value = response

        result = Agent(llm, repository).run("hello", Context())

        self.assertIs(result, response)
        llm.chat.assert_called_once_with(
            [{"role": "user", "content": "hello"}],
            tools=[{"name": "add", "description": "Add two numbers.", "parameters": {"type": "object"}}],
        )

    def test_run_keeps_messages_in_context(self):
        repository = self._repository()
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None))]
        )
        llm = Mock()
        llm.chat.return_value = response
        context = Context()
        agent = Agent(llm, repository)

        agent.run("first", context)
        agent.run("second", context)

        self.assertEqual(context.messages, [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ])
        self.assertEqual(llm.chat.call_args_list[1].args[0], context.messages)

    def test_calls_tool_and_continues_conversation(self):
        repository = self._repository()
        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(name="add", arguments='{"a": 2, "b": 3}'),
        )
        first_message = SimpleNamespace(content=None, tool_calls=[tool_call])
        first_response = SimpleNamespace(choices=[SimpleNamespace(message=first_message)])
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [first_response, final_response]

        result = Agent(llm, repository).run("add 2 and 3", Context())

        self.assertIs(result, final_response)
        self.assertEqual(llm.chat.call_count, 2)
        second_messages = llm.chat.call_args_list[1].args[0]
        self.assertEqual(second_messages[-1], {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": "5",
        })


if __name__ == "__main__":
    unittest.main()
