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
        self._loop = None
        self._loop_thread = None

    async def connect(self):
        if self._loop is not None:
            return self
        self._start_loop()
        future = asyncio.run_coroutine_threadsafe(self._connect_on_loop(), self._loop)
        try:
            await asyncio.wrap_future(future)
        except BaseException:
            self._stop_loop()
            raise
        return self

    async def _connect_on_loop(self):
        context = self.client if hasattr(self.client, "__aenter__") else None
        entered = False
        try:
            if context is not None:
                self._client_context = context
                self.client = await context.__aenter__()
                entered = True
            await self._refresh_on_loop()
        except BaseException as error:
            if context is not None and entered:
                try:
                    await context.__aexit__(type(error), error, error.__traceback__)
                except BaseException:
                    pass
            self._client_context = None
            raise

    async def refresh(self):
        if self._loop is not None:
            await self._submit(self._refresh_on_loop())
        else:
            await self._refresh_on_loop()
        return self

    async def _refresh_on_loop(self):
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

    async def close(self):
        if self._loop is None:
            return
        try:
            await self._submit(self._close_on_loop())
        finally:
            self._stop_loop()

    async def _close_on_loop(self):
        if self._client_context is not None:
            context = self._client_context
            self._client_context = None
            await context.__aexit__(None, None, None)

    def call(self, tool_name: str, **kwargs):
        if self.get_tool(tool_name) is None:
            raise ValueError(f"Tool '{tool_name}' not found.")
        if self._loop is not None:
            if threading.current_thread() is self._loop_thread:
                raise RuntimeError("Use async_call() from the MCP client event loop")
            future = asyncio.run_coroutine_threadsafe(
                self._call_on_loop(tool_name, kwargs), self._loop
            )
            return future.result()
        return _run_sync(self._call_on_loop(tool_name, kwargs))

    async def async_call(self, tool_name: str, **kwargs):
        if self.get_tool(tool_name) is None:
            raise ValueError(f"Tool '{tool_name}' not found.")
        if self._loop is not None:
            return await self._submit(self._call_on_loop(tool_name, kwargs))
        return await self._call_on_loop(tool_name, kwargs)

    async def _call_on_loop(self, tool_name: str, kwargs: dict):
        result = await self.client.call_tool(tool_name, kwargs)
        if getattr(result, "is_error", False):
            raise RuntimeError(_content_text(result))
        structured = getattr(result, "structured_content", None)
        if structured is not None:
            return structured
        return _content_text(result)

    async def _submit(self, coroutine):
        if threading.current_thread() is self._loop_thread:
            return await coroutine
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return await asyncio.wrap_future(future)

    def _start_loop(self):
        ready = threading.Event()

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._loop_thread = threading.current_thread()
            ready.set()
            loop.run_forever()
            loop.close()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        ready.wait()

    def _stop_loop(self):
        loop = self._loop
        thread = self._loop_thread
        if loop is None:
            return
        loop.call_soon_threadsafe(loop.stop)
        if thread is not threading.current_thread():
            thread.join()
        self._loop = None
        self._loop_thread = None

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
    awaitable.close()
    raise RuntimeError("Connect the MCPToolRepository before calling from an async loop")
