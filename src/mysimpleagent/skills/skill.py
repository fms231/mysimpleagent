class Skill:
    """A small set of instructions that can be injected into an Agent prompt."""

    def __init__(self, name: str, instructions: str, description: str = ""):
        self.name = name
        self.instructions = instructions
        self.description = description

    def to_prompt(self) -> str:
        title = f"## {self.name}"
        if self.description:
            title += f"\n{self.description}"
        return f"{title}\n{self.instructions}"
