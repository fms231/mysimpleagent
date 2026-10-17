import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from mysimpleagent.agent.agent import Agent
from mysimpleagent.context.context import Context
from mysimpleagent.tools.tool_repository import ToolRepository
from mysimpleagent.tools.tool_schema import ToolSchema
from mysimpleagent.tools.base_tools import BaseTools


class AgentTest(unittest.TestCase):
    def test_uses_base_tools_by_default(self):
        agent = Agent(Mock())

        self.assertIsInstance(agent.tools, BaseTools)
        self.assertEqual(
            {item["function"]["name"] for item in agent.tools.list_tools()},
            {"get_system_time", "read_file", "write_file"},
        )

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

        context = Context()
        context.add_message("user", "hello")
        result = Agent(llm, repository).run(context)

        self.assertIs(result, response)
        llm.chat.assert_called_once_with(
            [{"role": "user", "content": "hello"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers.",
                    "parameters": {"type": "object"},
                },
            }],
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

        context.add_message("user", "first")
        agent.run(context)
        context.add_message("user", "second")
        agent.run(context)

        self.assertEqual(context.messages, [
            {"id": 0, "role": "user", "content": "first"},
            {"id": 1, "role": "assistant", "content": ""},
            {"id": 2, "role": "user", "content": "second"},
            {"id": 3, "role": "assistant", "content": ""},
        ])
        self.assertEqual(llm.chat.call_args_list[1].args[0], [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "second"},
        ])

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

        context = Context()
        context.add_message("user", "add 2 and 3")
        result = Agent(llm, repository, max_tool_rounds=1).run(context)

        self.assertIs(result, final_response)
        self.assertEqual(llm.chat.call_count, 2)
        second_messages = llm.chat.call_args_list[1].args[0]
        self.assertIn({
            "role": "tool",
            "tool_call_id": "call-1",
            "content": "5",
        }, second_messages)


if __name__ == "__main__":
    unittest.main()
