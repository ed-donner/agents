"""
Module for defining and registering AI models used in the email campaign application.
"""

from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from .config import openrouter_api_key

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def normalize_chat_model(model_name: str, base_url: str | None, api_key: str | None):
    """Return model wrapper when an API key exists."""
    print(model_name, base_url, api_key)
    if not api_key:
        return None
    if base_url:
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    else:
        client = AsyncOpenAI(api_key=api_key)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


models = {
    "openai": "openai/gpt-4o",
    "gemini": "google/gemini-2.0-flash-001",
    "deepseek": "deepseek/deepseek-chat",
    "anthropic": "anthropic/claude-3.5-sonnet",
}

model_registry = {
    "openai": normalize_chat_model(models["openai"], OPENROUTER_BASE_URL, openrouter_api_key),
    "gemini": normalize_chat_model(models["gemini"], OPENROUTER_BASE_URL, openrouter_api_key),
    "deepseek": normalize_chat_model(models["deepseek"], OPENROUTER_BASE_URL, openrouter_api_key),
    "anthropic": normalize_chat_model(models["anthropic"], OPENROUTER_BASE_URL, openrouter_api_key),
}

available_models = {k: v for k, v in model_registry.items() if v is not None}

def get_model(provider_name: str):
    """Safely retrieve a model by provider name, falling back to gemini if missing."""
    if provider_name in available_models:
        return available_models[provider_name]
    if "gemini" in available_models:
        return available_models["gemini"]
    return next(iter(available_models.values()))

if not available_models:
    raise RuntimeError("No model keys found. Add at least one provider API key in .env.")
