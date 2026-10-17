# MySimpleAgent

一个基于 LiteLLM 的简单 Agent 项目，包含模型调用、工具调用、会话上下文和会话持久化。

## 安装

需要 Python 3.13 或更高版本，以及 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync
```

## 配置

在项目根目录创建 `.env`：

```env
MODEL_NAME=你的模型名称
BASE_URL=https://你的服务地址/v1
API_KEY=你的 API Key
```

`BASE_URL` 应填写服务的 API 根地址，LiteLLM 会自动追加具体接口路径。

## Python 用法

`main()` 会使用 `.env` 中的默认配置创建一个会话：

```python
from mysimpleagent import main

conversation = main()
response = conversation.send("你好")
print(response.choices[0].message.content)
```

也可以手动组装组件：

```python
from mysimpleagent.agent.agent import Agent
from mysimpleagent.conversation.conversation import Conversation
from mysimpleagent.llm.llm import LLM
from mysimpleagent.tools.tool_repository import ToolRepository

llm = LLM()
tools = ToolRepository()
agent = Agent(llm, tools)
conversation = Conversation(agent)
```

## 工具

如果创建 `Agent` 时不传入工具仓库，会自动注入 `BaseTools`，包含：

- `get_system_time`：获取系统时间
- `read_file`：读取 `output/` 下的 UTF-8 文件
- `write_file`：写入 `output/` 下的 UTF-8 文件

文件工具会拒绝访问 `output/` 目录之外的路径。自定义工具仓库可以通过 `Agent(llm, tools)` 传入。

工具由 `ToolRepository` 管理，工具描述使用 LiteLLM/OpenAI 兼容的 function 格式：

```python
from mysimpleagent.tools.tool_schema import ToolSchema

def add(a: int, b: int) -> int:
    return a + b

tool = ToolSchema()
tool.name = "add"
tool.description = "Add two numbers."
tool.func = add
tool.parameters = {
    "type": "object",
    "properties": {
        "a": {"type": "integer"},
        "b": {"type": "integer"},
    },
    "required": ["a", "b"],
}
tools.add_tool(tool)
```

`Agent` 会处理模型返回的工具调用，并将工具结果继续交给模型生成最终回答。

### MCP 工具

项目提供 `MCPToolRepository`，可以将 MCP Server 暴露的工具适配成当前 Agent 使用的工具格式。依赖已经包含官方 MCP Python SDK：

```python
from mcp import Client
from mysimpleagent import Agent, LLM, MCPToolRepository


async def create_agent():
    client = Client("http://localhost:8000/mcp")
    tools = MCPToolRepository(client)
    await tools.connect()
    return Agent(LLM(), tools), tools
```

`connect()` 会完成 MCP 握手并调用 `list_tools()`，之后 `Agent` 会通过 `MCPToolRepository.call()` 将工具调用转发给 MCP Server。使用完成后调用：

```python
await tools.close()
```

当前 `Agent.run()` 是同步方法，因此应在同步调用线程中使用 MCP 工具仓库；MCP 调用会在适配层内部等待异步结果。

## 可观测性

可以为 `Agent` 传入 `Observability`，通过生命周期事件处理器观察模型和工具调用：

```python
from mysimpleagent import Agent, Observability
from mysimpleagent.observability import LoggingObservabilityHandler

observability = Observability(handlers=[LoggingObservabilityHandler()])
agent = Agent(llm, tools, observability=observability)
```

可观测性会记录 `on_llm_start`、`on_llm_end`、`on_llm_error`，以及对应的工具调用事件。事件也会保存在 `observability.events` 中，便于接入自定义处理器。

## 会话持久化

每个 `Conversation` 都有独立的 `session_id`。每次调用 `send()` 后，消息会保存到：

```text
sessions/<session_id>.jsonl
```

使用相同的 `session_id` 可以恢复历史会话：

```python
conversation = Conversation(agent, session_id="my-session")
```

会话文件默认不提交到 Git。

## 前端

`front/` 中提供了一个简单的静态对话页面。页面会向以下接口发送请求：

```http
POST /api/chat
Content-Type: application/json
```

请求体：

```json
{
  "message": "你好",
  "messages": []
}
```

修改已有用户消息时，传入该消息在 context 中的零基索引 `edit_message_id`。后端会删除这条消息之后的旧回答，重新调用 Agent，并返回新的完整消息列表：

```json
{
  "message": "修改后的内容",
  "session_id": "已有会话 ID",
  "edit_message_id": 2
}
```

前端支持 `content`、`message`、`response` 和 OpenAI 风格的响应字段。

启动项目自带的 FastAPI 后端：

```bash
uv run uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

后端地址为 `http://localhost:8000`，前端页面会向该地址发送请求。

会话接口：

```http
GET /api/sessions
GET /api/sessions/<session_id>
```

前端启动时会读取会话列表，点击会话后加载对应的 JSONL 消息记录。空的会话文件会被忽略，新的空会话也不会写入文件。

FastAPI 文档地址：`http://localhost:8000/docs`

## 测试

运行不需要真实模型请求的测试：

```bash
uv run python -m unittest \
  src/mysimpleagent/agent/test/test_agent.py \
  src/mysimpleagent/agent/test/test_agent_errors.py \
  src/mysimpleagent/conversation/test/test_conversation.py \
  src/mysimpleagent/tools/test/test_tool_repository.py
```

LLM 集成测试会使用 `.env` 中的真实配置并发送请求：

```bash
uv run python -m unittest src/mysimpleagent/llm/test/test_llm.py
```
