class SystemPrompt:
    """Represents a system prompt sent as the first conversation message."""

    def __init__(self, content: str):
        self.content = content

    def to_message(self) -> dict[str, str]:
        return {"role": "system", "content": self.content}
