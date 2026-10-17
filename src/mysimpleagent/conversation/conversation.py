import re
from pathlib import Path
from uuid import uuid4

from ..agent.agent import Agent
from ..context.context import Context


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
        else:
            self.context = Context()
            if self.session_file.exists():
                self.context.load_from_file(str(self.session_file))

    def send(self, input_text: str):
        self.context.add_message("user", input_text)
        try:
            return self.agent.run(self.context)
        finally:
            if self.context.messages:
                self.context.save_to_file(str(self.session_file))

    def edit_and_send(self, message_id: int, input_text: str):
        self.context.replace_user_message(message_id, input_text)
        try:
            return self.agent.run(self.context)
        finally:
            if self.context.messages:
                self.context.save_to_file(str(self.session_file))
