import json


class Context:
    messages: list[dict[str, str]]

    def __init__(self, system_prompt: str | None = None):
        self.id = 0
        self.messages = []
        if system_prompt is not None:
            self.add_message("system", system_prompt)

    def add_message(self, role: str, content: str, **fields):
        message = {"id": self.id, "role": role, "content": content, **fields}
        self.id += 1
        self.messages.append(message)

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
        self.add_message("user", content)

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            for message in self.messages:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            messages = []
            for line in f:
                if line.strip():
                    message = json.loads(line)
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
        self.id = max((message["id"] for message in messages), default=-1) + 1

    def model_messages(self) -> list[dict]:
        return [{key: value for key, value in message.items() if key != "id"} for message in self.messages]
    
