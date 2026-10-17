import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from mysimpleagent.agent.agent import Agent
from mysimpleagent.context.context import Context
from mysimpleagent.tools.tool_repository import ToolRepository


class AgentToolErrorTest(unittest.TestCase):
    def test_non_serializable_tool_result_becomes_tool_error_without_retry(self):
        call = SimpleNamespace(
            id="datetime-result",
            function=SimpleNamespace(name="now", arguments="{}"),
        )
        tool_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[call]))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [tool_response, final_response]
        tools = ToolRepository()
        tool = Mock()
        tool.name = "now"
        tool.description = "return time"
        tool.parameters = {"type": "object"}
        tool.func.return_value = datetime.now()
        tools.add_tool(tool)
        context = Context()

        result = Agent(llm, tools, max_tool_rounds=2).run(context)

        self.assertIs(result, final_response)
        tool.func.assert_called_once_with()
        tool_message = [message for message in context.messages if message["role"] == "tool"][0]
        self.assertEqual(tool_message["role"], "tool")
        self.assertIn("could not be serialized", tool_message["content"])

    def test_after_hook_error_does_not_repeat_successful_tool(self):
        call = SimpleNamespace(
            id="side-effect",
            function=SimpleNamespace(name="write", arguments='{"value": 1}'),
        )
        tool_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[call]))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [tool_response, final_response]
        tools = ToolRepository()
        tool = Mock()
        tool.name = "write"
        tool.description = "write with side effects"
        tool.parameters = {"type": "object"}
        tool.func.return_value = "written"
        tools.add_tool(tool)
        hook = Mock()
        hook.after_tool_call.side_effect = RuntimeError("post-processing failed")

        Agent(llm, tools, max_tool_rounds=2, hooks=[hook]).run(Context())

        tool.func.assert_called_once_with(value=1)

    def test_error_hook_gets_arguments_from_current_invalid_call(self):
        calls = [
            SimpleNamespace(
                id="first",
                function=SimpleNamespace(name="first", arguments='{"value": 1}'),
            ),
            SimpleNamespace(
                id="bad-json",
                function=SimpleNamespace(name="second", arguments="not-json"),
            ),
        ]
        response_with_tools = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=calls))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [response_with_tools, final_response]
        tools = ToolRepository()
        for name in ("first", "second"):
            tool = Mock()
            tool.name = name
            tool.description = name
            tool.parameters = {"type": "object"}
            tool.func.return_value = "ok"
            tools.add_tool(tool)

        hook = Mock()
        Agent(llm, tools, hooks=[hook]).run(Context())

        self.assertEqual(hook.on_tool_error.call_args.args[1], {})

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

        context.add_message("user", "try tools")
        result = Agent(llm, ToolRepository()).run(context)

        self.assertIs(result, final_response)
        tool_messages = [message for message in context.messages if message["role"] == "tool"]
        self.assertEqual(len(tool_messages), 2)
        self.assertEqual(tool_messages[0]["tool_call_id"], "bad-json")
        self.assertIn("unavailable", tool_messages[0]["content"])
        self.assertEqual(tool_messages[1]["tool_call_id"], "unknown-tool")
        self.assertIn("Tool 'missing' not found.", tool_messages[1]["content"])

    def test_retries_failed_tool_and_reports_unavailable_after_limit(self):
        calls = [SimpleNamespace(
            id="unstable-1",
            function=SimpleNamespace(name="unstable", arguments="{}"),
        )]
        first_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=calls))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )
        llm = Mock()
        llm.chat.side_effect = [first_response, final_response]
        tools = ToolRepository()
        context = Context()
        tool = Mock()
        tool.name = "unstable"
        tool.description = "Always fails"
        tool.parameters = {"type": "object"}
        tool.func.side_effect = RuntimeError("temporary failure")
        tools.add_tool(tool)

        context.add_message("user", "try")
        result = Agent(llm, tools, max_tool_rounds=2).run(context)

        self.assertIs(result, final_response)
        self.assertEqual(tool.func.call_count, 3)
        tool_message = [
            message for message in llm.chat.call_args_list[1].args[0]
            if message["role"] == "tool"
        ][0]
        self.assertEqual(tool_message["role"], "tool")
        self.assertIn("unavailable", tool_message["content"])


if __name__ == "__main__":
    unittest.main()
