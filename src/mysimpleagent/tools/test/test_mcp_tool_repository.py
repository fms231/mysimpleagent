import asyncio
import threading
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


class ContextMCPClient(FakeMCPClient):
    def __init__(self, fail_discovery=False):
        self.fail_discovery = fail_discovery
        self.entered = False
        self.exited = False
        self.call_thread = None

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.exited = True

    async def list_tools(self):
        if self.fail_discovery:
            raise RuntimeError("discovery failed")
        return await super().list_tools()

    async def call_tool(self, name, arguments):
        self.call_thread = threading.current_thread()
        return await super().call_tool(name, arguments)

class MCPToolRepositoryTest(unittest.TestCase):
    def test_connect_closes_client_when_discovery_fails(self):
        client = ContextMCPClient(fail_discovery=True)
        repository = MCPToolRepository(client)

        with self.assertRaisesRegex(RuntimeError, "discovery failed"):
            asyncio.run(repository.connect())

        self.assertTrue(client.entered)
        self.assertTrue(client.exited)

    def test_connected_calls_run_on_persistent_client_loop(self):
        client = ContextMCPClient()
        repository = MCPToolRepository(client)

        async def exercise():
            await repository.connect()
            result = repository.call("add", a=2, b=3)
            await repository.close()
            return result

        self.assertEqual(asyncio.run(exercise()), {"result": 5})
        self.assertTrue(client.exited)
        self.assertIsNotNone(client.call_thread)

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
