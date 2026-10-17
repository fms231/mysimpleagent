import asyncio
import threading
from collections.abc import Awaitable
from typing import Any

from .tool_repository import ToolRepository
from .tool_schema import ToolSchema


class MCPToolRepository(ToolRepository):
    """Expose tools discovered from an MCP client through ToolRepository."""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self._client_context = None

    async def connect(self):
        if hasattr(self.client, "__aenter__"):
            self._client_context = self.client
            self.client = await self.client.__aenter__()
        await self.refresh()
        return self

    async def refresh(self):
        result = await self.client.list_tools()
        tools = getattr(result, "tools", result)
        self.tools.clear()
        for remote_tool in tools:
            schema = ToolSchema()
            schema.name = remote_tool.name
            schema.description = getattr(remote_tool, "description", "") or ""
            schema.parameters = getattr(remote_tool, "inputSchema", None) or {
                "type": "object"
            }
            schema.func = self._unsupported_local_call
            self.add_tool(schema)
        return self

    async def close(self):
        if self._client_context is not None:
            await self._client_context.__aexit__(None, None, None)
            self._client_context = None

    def call(self, tool_name: str, **kwargs):
        if self.get_tool(tool_name) is None:
            raise ValueError(f"Tool '{tool_name}' not found.")
        result = _run_sync(self.client.call_tool(tool_name, kwargs))
        if getattr(result, "is_error", False):
            raise RuntimeError(_content_text(result))
        structured = getattr(result, "structured_content", None)
        if structured is not None:
            return structured
        return _content_text(result)

    @staticmethod
    def _unsupported_local_call(**kwargs):
        raise RuntimeError("MCP tools must be called through MCPToolRepository")


def _content_text(result: Any) -> str:
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content
    parts = []
    for item in content or []:
        text = getattr(item, "text", None)
        parts.append(text if text is not None else str(item))
    return "\n".join(parts)


def _run_sync(awaitable: Awaitable):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result = []
    error = []

    def run_in_thread():
        try:
            result.append(asyncio.run(awaitable))
        except BaseException as exc:
            error.append(exc)

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result[0]
