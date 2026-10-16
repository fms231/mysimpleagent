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

前端支持 `content`、`message`、`response` 和 OpenAI 风格的响应字段。

启动项目自带的本地后端：

```bash
uv run python backend/server.py
```

后端地址为 `http://localhost:8000`，前端页面会向该地址发送请求。

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
