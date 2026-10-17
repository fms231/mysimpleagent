from .agent.agent import Agent
from .conversation.conversation import Conversation
from .llm.llm import LLM
from .tools.tool_repository import ToolRepository
from .hooks import ToolHook
from .context.context_strategy import ContextStrategy


def main() -> Conversation:
    llm = LLM()
    tools = ToolRepository()
    agent = Agent(llm, tools)
    conversation = Conversation(agent)

    print("mysimpleagent initialized")
    return conversation
