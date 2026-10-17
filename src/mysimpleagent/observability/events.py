from dataclasses import dataclass
from copy import deepcopy
from typing import Any


@dataclass
class LLMStartEvent:
    model: str
    messages: list[dict]

    def __post_init__(self):
        self.messages = deepcopy(self.messages)


@dataclass
class LLMEndEvent:
    model: str
    response: Any
    duration_ms: float


@dataclass
class LLMErrorEvent:
    model: str
    error: Exception
    duration_ms: float


@dataclass
class ToolStartEvent:
    name: str
    arguments: dict


@dataclass
class ToolEndEvent:
    name: str
    arguments: dict
    result: Any
    duration_ms: float


@dataclass
class ToolErrorEvent:
    name: str
    arguments: dict
    error: Exception
    duration_ms: float
