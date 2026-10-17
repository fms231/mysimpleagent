import logging

import litellm


logger = logging.getLogger(__name__)


class ContextStrategy:
    """Apply a context policy before each model request."""

    threshold = 0.8

    def __init__(self, model: str, max_context: int | None):
        self.model = model
        self.max_context = max_context

    def check(self, context) -> bool:
        """Log when context usage reaches the threshold; return whether triggered."""
        max_context = self.max_context
        if not isinstance(max_context, (int, float)) or max_context <= 0:
            return False
        try:
            input_tokens = litellm.token_counter(
                model=self.model,
                messages=context.model_messages(),
            )
        except Exception:
            return False
        if input_tokens >= max_context * self.threshold:
            logger.error(
                "Context usage reached %.1f%% (%s/%s tokens)",
                input_tokens / max_context * 100,
                input_tokens,
                max_context,
            )
            return True
        return False
