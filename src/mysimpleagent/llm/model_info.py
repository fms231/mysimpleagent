def get_model_metadata(model: str) -> dict:
    """Return model metadata provided by LiteLLM for ``model``."""
    import litellm

    return litellm.get_model_info(model)
