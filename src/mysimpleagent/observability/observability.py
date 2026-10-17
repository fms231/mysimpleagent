import logging
from dataclasses import asdict, is_dataclass
from typing import Any


logger = logging.getLogger(__name__)


class Observability:
    """Dispatch LLM and tool lifecycle events to registered handlers."""

    def __init__(self, handlers: list | None = None, max_events: int | None = None):
        if max_events is not None and max_events < 0:
            raise ValueError("max_events must be non-negative or None")
        self.handlers = handlers or []
        self.max_events = max_events
        self.events: list[Any] = []

    def emit(self, method_name: str, event):
        if self.max_events != 0:
            self.events.append(event)
        for handler in self.handlers:
            callback = getattr(handler, method_name, None)
            if callback is None:
                continue
            try:
                callback(event)
            except Exception:
                logger.exception("Observability handler failed: %s", method_name)
        if self.max_events is not None and len(self.events) > self.max_events:
            del self.events[:-self.max_events]

    def event_dicts(self) -> list[dict]:
        return [asdict(event) if is_dataclass(event) else dict(event) for event in self.events]
