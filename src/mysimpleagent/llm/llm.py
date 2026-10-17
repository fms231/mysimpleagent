import litellm
from dotenv import load_dotenv
import os

from .llm_config import LLMConfig
from .model_info import get_model_metadata

load_dotenv()


class LLM(LLMConfig):
    def __init__(self, model: str = None, base_url: str = None,
                 api_key: str = None, max_context: int = None,
                 ):
        if base_url is not None:
            self.base_url = base_url
        else:
            self.base_url = os.getenv("BASE_URL", "")
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("API_KEY", "")
        self.model = model or os.getenv("MODEL_NAME")
        if not self.model:
            raise ValueError("MODEL_NAME must be set in the environment.")
        try:
            metadata = get_model_metadata(self.model)
        except Exception:
            metadata = {}
        self.max_input_tokens = metadata.get("max_input_tokens")
        self.max_output_tokens = metadata.get("max_output_tokens")
        model_context = metadata.get("max_context_window")
        if model_context is None and self.max_input_tokens and self.max_output_tokens:
            model_context = self.max_input_tokens + self.max_output_tokens
        if model_context is None:
            model_context = metadata.get("max_tokens")
        if max_context is not None and model_context is not None and max_context > model_context:
            raise ValueError("max_context exceeds model context limit")
        self.max_context = max_context if max_context is not None else model_context

    def get_model_metadata(self) -> dict:
        """Return model metadata provided by LiteLLM for the current model."""
        return get_model_metadata(self.model)

    def get_max_tokens(self) -> int | None:
        """Return the configured total context limit."""
        return self.max_context

    def get_max_output_tokens(self) -> int | None:
        """Return the model's maximum output token limit."""
        return self.max_output_tokens

    def chat(self, messages: list[dict], **kwargs):
        """Send a chat request through LiteLLM and return its response."""
        params = {
            "model": self.model,
            "messages": messages,
            "api_base": self.base_url,
            "api_key": self.api_key,
            **kwargs,
        }
        if self.max_context is not None and "max_tokens" not in kwargs:
            input_tokens = litellm.token_counter(model=self.model, messages=messages)
            remaining_tokens = self.max_context - input_tokens
            if remaining_tokens <= 0:
                raise ValueError("The input exceeds the configured context limit")
            params["max_tokens"] = min(
                remaining_tokens,
                self.max_output_tokens or remaining_tokens,
            )

        return litellm.completion(
            **params,
        )
        
