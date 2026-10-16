import json


class Context:
    messages: list[dict[str, str]]

    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            for message in self.messages:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            self.messages = []
            for line in f:
                if line.strip():
                    self.messages.append(json.loads(line))
    
