from src.agent.agent import Agent
from src.conversation.conversation import Conversation
from src.llm.llm import LLM
from src.tools.tool_repository import ToolRepository


def main() -> Conversation:
    llm = LLM()
    tools = ToolRepository()
    agent = Agent(llm, tools)
    conversation = Conversation(agent)

    print("mysimpleagent initialized")
    return conversation
