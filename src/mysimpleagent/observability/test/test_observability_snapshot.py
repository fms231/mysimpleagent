import unittest
import logging
from types import SimpleNamespace

from mysimpleagent.agent.agent import Agent
from mysimpleagent.context.context import Context
from mysimpleagent.observability import Observability
from mysimpleagent.observability.logging_handler import LoggingObservabilityHandler
from mysimpleagent.observability.events import ToolEndEvent, ToolStartEvent
from mysimpleagent.observability.events import LLMEndEvent
from mysimpleagent.tools.tool_repository import ToolRepository
from mysimpleagent.tools.tool_schema import ToolSchema


class RedactingHandler:
    def on_llm_start(self, event):
        event.messages[0]["content"] = "redacted"


class SnapshotTest(unittest.TestCase):
    def test_observability_can_bound_retained_events(self):
        observability = Observability(max_events=2)

        observability.emit("on_llm_end", LLMEndEvent("model", "one", 1))
        observability.emit("on_llm_end", LLMEndEvent("model", "two", 2))
        observability.emit("on_llm_end", LLMEndEvent("model", "three", 3))

        self.assertEqual([event.response for event in observability.events], ["two", "three"])

    def test_logging_handler_does_not_log_tool_payloads_by_default(self):
        handler = LoggingObservabilityHandler()

        with self.assertLogs("mysimpleagent.observability.logging_handler", level=logging.INFO) as logs:
            handler.on_tool_start(ToolStartEvent("write_file", {"content": "secret"}))
            handler.on_tool_end(ToolEndEvent("read_file", {}, "secret result", 1.2))

        output = "\n".join(logs.output)
        self.assertIn("write_file", output)
        self.assertIn("read_file", output)
        self.assertNotIn("secret", output)

    def test_llm_handler_cannot_change_pending_request(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))]
        )

        class LLM:
            model = "test-model"

            def chat(self, messages, **kwargs):
                self.messages = messages
                return response

        llm = LLM()
        context = Context()
        context.add_message("user", "secret")

        Agent(llm, observability=Observability([RedactingHandler()])).run(context)

        self.assertEqual(llm.messages[0]["content"], "secret")

    def test_unserializable_tool_result_emits_only_tool_error(self):
        tool = ToolSchema()
        tool.name = "returns_object"
        tool.description = ""
        tool.parameters = {"type": "object"}
        tool.func = lambda: object()
        tools = ToolRepository()
        tools.add_tool(tool)

        call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(name="returns_object", arguments="{}"),
        )
        first_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[call]))]
        )
        final_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=None))]
        )

        class LLM:
            model = "test-model"

            def __init__(self):
                self.responses = iter([first_response, final_response])

            def chat(self, messages, **kwargs):
                return next(self.responses)

        observability = Observability()
        context = Context()
        Agent(LLM(), tools, observability=observability).run(context)

        tool_events = [event.__class__.__name__ for event in observability.events]
        self.assertEqual(tool_events, [
            "LLMStartEvent", "LLMEndEvent", "ToolStartEvent", "ToolErrorEvent",
            "LLMStartEvent", "LLMEndEvent",
        ])


if __name__ == "__main__":
    unittest.main()
