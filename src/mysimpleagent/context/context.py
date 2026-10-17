import json
from copy import deepcopy

from ..systemprompt import SystemPrompt


class Context:
    messages: list[dict[str, str]]

    def __init__(
        self,
        system_prompt: str | SystemPrompt | None = None,
        context_strategy=None,
    ):
        self.id = 0
        self.messages = []
        self.model_message = []
        self.context_strategy = context_strategy
        if isinstance(system_prompt, SystemPrompt):
            self.system_prompt = system_prompt.content
        else:
            self.system_prompt = system_prompt

    def _refresh_model_messages(self):
        self.model_message = [
            {key: value for key, value in message.items() if key != "id"}
            for message in self.messages
        ]

    def add_message(self, role: str, content: str, **fields):
        message = {"id": self.id, "role": role, "content": content, **fields}
        self.id += 1
        self.messages.append(message)
        self.model_message.append({key: value for key, value in message.items() if key != "id"})
        if self.context_strategy is not None:
            self.context_strategy.check(self)

    def replace_user_message(self, message_id: int, content: str):
        message_index = next(
            (index for index, message in enumerate(self.messages) if message.get("id") == message_id),
            None,
        )
        if message_index is None:
            raise IndexError("Message id out of range")
        if self.messages[message_index].get("role") != "user":
            raise ValueError("Only user messages can be replaced")
        self.messages = self.messages[:message_index]
        self._refresh_model_messages()
        self.add_message("user", content)

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            if self.system_prompt is not None:
                f.write(json.dumps(
                    {"_context": {"system_prompt": self.system_prompt}},
                    ensure_ascii=False,
                ) + "\n")
            for message in self.messages:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            messages = []
            system_prompt = self.system_prompt
            for line in f:
                if line.strip():
                    message = json.loads(line)
                    if "_context" in message:
                        system_prompt = message["_context"].get("system_prompt")
                        continue
                    messages.append(message)
        reserved_ids = {message["id"] for message in messages if "id" in message}
        assigned_ids = set()
        next_id = 0
        for message in messages:
            if "id" in message and message["id"] not in assigned_ids:
                assigned_ids.add(message["id"])
                continue
            while next_id in reserved_ids or next_id in assigned_ids:
                next_id += 1
            message["id"] = next_id
            assigned_ids.add(next_id)
            next_id += 1
        self.messages = messages
        self.system_prompt = system_prompt
        self.id = max((message["id"] for message in messages), default=-1) + 1
        self._refresh_model_messages()

    def model_messages(self, extra_system_prompts: list[str] | None = None) -> list[dict]:
        prompts = [self.system_prompt, *(extra_system_prompts or [])]
        prompts = [prompt for prompt in prompts if prompt]
        if not prompts:
            return deepcopy(self.model_message)

        system_message = {"role": "system", "content": "\n\n".join(prompts)}
        return [system_message, *deepcopy(self.model_message)]
    
