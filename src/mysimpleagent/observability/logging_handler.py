import logging
from collections.abc import Callable


logger = logging.getLogger(__name__)


class LoggingObservabilityHandler:
    def __init__(self, payload_redactor: Callable | None = None):
        """Log metadata; payloads are logged only after explicit redaction."""
        self.payload_redactor = payload_redactor

    def _payload(self, value):
        if self.payload_redactor is None:
            return None
        return self.payload_redactor(value)

    def on_llm_start(self, event):
        logger.info("LLM started: model=%s", event.model)

    def on_llm_end(self, event):
        logger.info("LLM finished: model=%s duration_ms=%.2f", event.model, event.duration_ms)

    def on_llm_error(self, event):
        logger.error("LLM failed: model=%s duration_ms=%.2f error=%s", event.model, event.duration_ms, event.error)

    def on_tool_start(self, event):
        payload = self._payload(event.arguments)
        if payload is None:
            logger.info("Tool started: name=%s", event.name)
        else:
            logger.info("Tool started: name=%s arguments=%s", event.name, payload)

    def on_tool_end(self, event):
        payload = self._payload(event.result)
        if payload is None:
            logger.info("Tool finished: name=%s duration_ms=%.2f", event.name, event.duration_ms)
        else:
            logger.info("Tool finished: name=%s duration_ms=%.2f result=%s", event.name, event.duration_ms, payload)

    def on_tool_error(self, event):
        payload = self._payload(str(event.error))
        if payload is None:
            logger.error("Tool failed: name=%s duration_ms=%.2f", event.name, event.duration_ms)
        else:
            logger.error("Tool failed: name=%s duration_ms=%.2f error=%s", event.name, event.duration_ms, payload)
