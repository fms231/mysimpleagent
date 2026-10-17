import logging
from dataclasses import asdict, is_dataclass
from typing import Any


logger = logging.getLogger(__name__)


class Observability:
    """Dispatch LLM and tool lifecycle events to registered handlers."""

    def __init__(self, handlers: list | None = None):
        self.handlers = handlers or []
        self.events: list[Any] = []

    def emit(self, method_name: str, event):
        self.events.append(event)
        for handler in self.handlers:
            callback = getattr(handler, method_name, None)
            if callback is None:
                continue
            try:
                callback(event)
            except Exception:
                logger.exception("Observability handler failed: %s", method_name)

    def event_dicts(self) -> list[dict]:
        return [asdict(event) if is_dataclass(event) else dict(event) for event in self.events]
