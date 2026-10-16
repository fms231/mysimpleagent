from typing import Any, Callable

class ToolSchema:
    name: str
    description: str
    func: Callable
    parameters: dict[str, Any]