import asyncio
import unittest
from types import SimpleNamespace

from mysimpleagent.tools.mcp_tool_repository import MCPToolRepository


class FakeMCPClient:
    async def list_tools(self):
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name="add",
                    description="Add two numbers.",
                    inputSchema={
                        "type": "object",
                        "properties": {"a": {"type": "integer"}},
                    },
                )
            ]
        )

    async def call_tool(self, name, arguments):
        return SimpleNamespace(
            structured_content={"result": arguments["a"] + arguments["b"]},
            content=[],
            is_error=False,
        )


class MCPToolRepositoryTest(unittest.TestCase):
    def test_refresh_converts_mcp_tools_to_function_schemas(self):
        repository = MCPToolRepository(FakeMCPClient())

        asyncio.run(repository.refresh())

        self.assertEqual(repository.list_tools(), [{
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "integer"}},
                },
            },
        }])

    def test_call_returns_structured_mcp_content(self):
        repository = MCPToolRepository(FakeMCPClient())
        asyncio.run(repository.refresh())

        result = repository.call("add", a=2, b=3)

        self.assertEqual(result, {"result": 5})


if __name__ == "__main__":
    unittest.main()
