from ..agent.agent import Agent
from ..context.context import Context


class Conversation:
    def __init__(self, agent: Agent, context: Context | None = None):
        self.agent = agent
        self.context = context or Context()

    def send(self, input_text: str):
        return self.agent.run(input_text, self.context)
