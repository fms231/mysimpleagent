def get_model_metadata(model: str) -> dict:
    """Return model metadata provided by LiteLLM for ``model``."""
    import litellm

    return litellm.get_model_info(model)


def get_model_context_limit(metadata: dict) -> int | None:
    """Resolve the model's total context limit using one shared priority."""
    context_window = metadata.get("max_context_window")
    if isinstance(context_window, int) and context_window > 0:
        return context_window

    input_tokens = metadata.get("max_input_tokens")
    output_tokens = metadata.get("max_output_tokens")
    if isinstance(input_tokens, int) and input_tokens > 0:
        if isinstance(output_tokens, int) and output_tokens > 0:
            return input_tokens + output_tokens
        return input_tokens

    max_tokens = metadata.get("max_tokens")
    if isinstance(max_tokens, int) and max_tokens > 0:
        return max_tokens
    return None
