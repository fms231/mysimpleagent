from typing import Any


class ToolRepository():
    def __init__(self):
        self.tools = {}

    def add_tool(self, tool):
        self.tools[tool.name] = tool

    def get_tool(self, tool_name):
        return self.tools.get(tool_name)

    def list_tools(self) -> list[dict[str, Any]]:
        result = []
        for tool in self.tools.values():
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return result

    def call(self, tool_name: str, **kwargs):
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        return tool.func(**kwargs)
