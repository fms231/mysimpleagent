import litellm
from dotenv import load_dotenv
import os

from .llm_config import LLMConfig
from .model_info import get_model_metadata

load_dotenv()


class LLM(LLMConfig):
    def __init__(self, model: str = None, base_url: str = None,
                 api_key: str = None, max_tokens: int = None,
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
        if max_tokens is not None:
            self.max_tokens = max_tokens
        else:
            try:
                self.max_tokens = get_model_metadata(self.model).get("max_tokens")
            except Exception:
                self.max_tokens = None

    def get_model_metadata(self) -> dict:
        """Return model metadata provided by LiteLLM for the current model."""
        return get_model_metadata(self.model)

    def get_max_tokens(self) -> int | None:
        """Return the maximum number of tokens for the current model."""
        return self.max_tokens

    def chat(self, messages: list[dict], **kwargs):
        """Send a chat request through LiteLLM and return its response."""
        params = {
            "model": self.model,
            "messages": messages,
            "api_base": self.base_url,
            "api_key": self.api_key,
            **kwargs,
        }
        if self.max_tokens is not None and "max_tokens" not in kwargs:
            params["max_tokens"] = self.max_tokens

        return litellm.completion(
            **params,
        )
        
