import re
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from ..agent.agent import Agent
from ..context.context import Context
from ..context.context_strategy import ContextStrategy


class Conversation:
    def __init__(
        self,
        agent: Agent,
        context: Context | None = None,
        session_id: str | None = None,
        sessions_dir: str = "sessions",
    ):
        self.agent = agent
        self.session_id = session_id or uuid4().hex
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.session_id):
            raise ValueError("Invalid session_id")
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.sessions_dir / f"{self.session_id}.jsonl"

        if context is not None:
            self.context = context
            if self.context.context_strategy is None:
                self.context.context_strategy = self._make_context_strategy()
        else:
            self.context = Context(context_strategy=self._make_context_strategy())
            if self.session_file.exists():
                self.context.load_from_file(str(self.session_file))

    def _make_context_strategy(self):
        model = getattr(self.agent.llm, "model", None)
        max_context = getattr(self.agent.llm, "max_context", None)
        if model and isinstance(max_context, (int, float)) and max_context > 0:
            return ContextStrategy(model, max_context)
        return None

    def send(self, input_text: str):
        previous_messages = deepcopy(self.context.messages)
        previous_id = self.context.id
        try:
            self.context.add_message("user", input_text)
            response = self.agent.run(self.context)
        except Exception:
            self.context.messages = previous_messages
            self.context.id = previous_id
            raise
        if self.context.messages:
            self.context.save_to_file(str(self.session_file))
        return response

    def edit_and_send(self, message_id: int, input_text: str):
        previous_messages = deepcopy(self.context.messages)
        previous_id = self.context.id
        try:
            self.context.replace_user_message(message_id, input_text)
            response = self.agent.run(self.context)
        except Exception:
            self.context.messages = previous_messages
            self.context.id = previous_id
            raise
        if self.context.messages:
            self.context.save_to_file(str(self.session_file))
        return response
