import logging


logger = logging.getLogger(__name__)


class LoggingObservabilityHandler:
    def on_llm_start(self, event):
        logger.info("LLM started: model=%s", event.model)

    def on_llm_end(self, event):
        logger.info("LLM finished: model=%s duration_ms=%.2f", event.model, event.duration_ms)

    def on_llm_error(self, event):
        logger.error("LLM failed: model=%s duration_ms=%.2f error=%s", event.model, event.duration_ms, event.error)

    def on_tool_start(self, event):
        logger.info("Tool started: name=%s arguments=%s", event.name, event.arguments)

    def on_tool_end(self, event):
        logger.info("Tool finished: name=%s duration_ms=%.2f result=%s", event.name, event.duration_ms, event.result)

    def on_tool_error(self, event):
        logger.error("Tool failed: name=%s duration_ms=%.2f error=%s", event.name, event.duration_ms, event.error)
