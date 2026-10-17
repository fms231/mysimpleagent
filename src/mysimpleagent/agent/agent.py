import json
import logging

from ..context.context import Context
from ..tools.base_tools import BaseTools
from ..tools.tool_repository import ToolRepository


logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        llm,
        tools: ToolRepository | None = None,
        max_tool_rounds: int = 10,
        hooks: list | None = None,
    ):
        self.llm = llm
        self.tools = tools if tools is not None else BaseTools()
        self.max_tool_rounds = max_tool_rounds
        self.hooks = hooks or []

    def run(self, context: Context):
        while True:
            response = self.llm.chat(
                context.model_messages(),
                tools=self.tools.list_tools(),
            )

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                context.add_message("assistant", getattr(message, "content", None) or "")
                return response

            context.add_message(
                "assistant",
                getattr(message, "content", None),
                tool_calls=[
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            )

            for call in tool_calls:
                result = None
                for attempt in range(self.max_tool_rounds + 1):
                    arguments = {}
                    try:
                        arguments = json.loads(call.function.arguments)
                        for hook in self.hooks:
                            hook.before_tool_call(call.function.name, arguments, context)
                    except Exception as error:
                        for hook in self.hooks:
                            hook.on_tool_error(call.function.name, arguments, error, context)
                        if attempt == self.max_tool_rounds:
                            result = (
                                f"Tool '{call.function.name}' is unavailable after "
                                f"{self.max_tool_rounds} failed retries: {error}"
                            )
                        continue

                    try:
                        result = self.tools.call(call.function.name, **arguments)
                    except Exception as error:
                        for hook in self.hooks:
                            hook.on_tool_error(call.function.name, arguments, error, context)
                        if attempt == self.max_tool_rounds:
                            result = (
                                f"Tool '{call.function.name}' is unavailable after "
                                f"{self.max_tool_rounds} failed retries: {error}"
                            )
                        continue

                    for hook in self.hooks:
                        try:
                            hook.after_tool_call(call.function.name, arguments, result, context)
                        except Exception:
                            logger.exception("after_tool_call hook failed for tool '%s'", call.function.name)
                    if not isinstance(result, str):
                        try:
                            result = json.dumps(result, ensure_ascii=False)
                        except Exception as error:
                            for hook in self.hooks:
                                hook.on_tool_error(call.function.name, arguments, error, context)
                            result = (
                                f"Tool '{call.function.name}' result could not be serialized: "
                                f"{error}"
                            )
                    break
                context.add_message("tool", result, tool_call_id=call.id)


