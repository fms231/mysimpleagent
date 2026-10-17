import json

from ..context.context import Context
from ..tools.base_tools import BaseTools
from ..tools.tool_repository import ToolRepository


class Agent:
    def __init__(
        self,
        llm,
        tools: ToolRepository | None = None,
        max_tool_rounds: int = 10,
    ):
        self.llm = llm
        self.tools = tools if tools is not None else BaseTools()
        self.max_tool_rounds = max_tool_rounds

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
                    try:
                        arguments = json.loads(call.function.arguments)
                        result = self.tools.call(call.function.name, **arguments)
                        if not isinstance(result, str):
                            result = json.dumps(result, ensure_ascii=False)
                        break
                    except Exception as error:
                        if attempt == self.max_tool_rounds:
                            result = (
                                f"Tool '{call.function.name}' is unavailable after "
                                f"{self.max_tool_rounds} failed retries: {error}"
                            )
                context.add_message("tool", result, tool_call_id=call.id)

