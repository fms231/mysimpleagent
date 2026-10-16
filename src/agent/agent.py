import json

from src.context.context import Context
from src.tools.tool_repository import ToolRepository


class Agent:
    def __init__(
        self,
        llm,
        tools: ToolRepository,
        max_tool_rounds: int = 10,
    ):
        self.llm = llm
        self.tools = tools
        self.max_tool_rounds = max_tool_rounds

    def run(self, input_text: str, context: Context):
        context.add_message("user", input_text)

        for _ in range(self.max_tool_rounds):
            response = self.llm.chat(
                context.messages,
                tools=self.tools.list_tools(),
            )

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                return response

            context.messages.append({
                "role": "assistant",
                "content": getattr(message, "content", None),
                "tool_calls": [
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
            })

            for call in tool_calls:
                arguments = json.loads(call.function.arguments)
                result = self.tools.call(call.function.name, **arguments)
                if not isinstance(result, str):
                    result = json.dumps(result, ensure_ascii=False)
                context.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

        raise RuntimeError("Maximum tool call rounds exceeded.")
