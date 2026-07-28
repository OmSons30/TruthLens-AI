import logging
from config import settings
from services.models.base import BaseModelAdapter
from services.models.openai import OpenAIAdapter
from services.models.ollama import OllamaAdapter

logger = logging.getLogger("truthlens_model_router")

# Map of model keys (which matches frontend selection) to their adapter initialization.
# Keys:
# - 'openai-gpt-4o'
# - 'ollama-llama3.1'
# - 'ollama-mistral'
# - 'ollama-gemma3'
# - 'ollama-deepseek-r1'

def get_model_adapter(model_key: str) -> BaseModelAdapter:
    """
    Factory function to retrieve model adapters based on the chosen key.
    """
    key_lower = model_key.lower()
    
    if key_lower == "openai-gpt-4o":
        return OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL # Will default to settings.OPENAI_MODEL (e.g. gpt-4o or gpt-4o-mini)
        )
    elif key_lower == "ollama-llama3.1":
        model_name = getattr(settings, "OLLAMA_LLAMA_MODEL", "llama3.1")
        return OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_name=model_name)
    elif key_lower == "ollama-mistral":
        model_name = getattr(settings, "OLLAMA_MISTRAL_MODEL", "mistral")
        return OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_name=model_name)
    elif key_lower == "ollama-gemma3":
        model_name = getattr(settings, "OLLAMA_GEMMA_MODEL", "gemma3")
        return OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_name=model_name)
    elif key_lower == "ollama-deepseek-r1":
        model_name = getattr(settings, "OLLAMA_DEEPSEEK_MODEL", "deepseek-r1")
        return OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_name=model_name)
    else:
        logger.warning(f"Unsupported model key received: {model_key}. Defaulting to OpenAI.")
        return OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL
        )
