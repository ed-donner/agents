"""
Module for defining and registering AI models used in the email campaign application.
"""

from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from config import openrouter_api_key


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def make_chat_model(model_name: str, base_url: str, api_key: str):
    """Return chat model"""
    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


models = {
    "openai": "openai/gpt-4o",
    "gemini": "google/gemini-2.0-flash-001",
    "deepseek": "deepseek/deepseek-chat",
    "anthropic": "anthropic/claude-3.5-sonnet",
}

model_registry = {
    "openai": make_chat_model(models["openai"], OPENROUTER_BASE_URL, openrouter_api_key),
    "gemini": make_chat_model(models["gemini"], OPENROUTER_BASE_URL, openrouter_api_key),
    "deepseek": make_chat_model(models["deepseek"], OPENROUTER_BASE_URL, openrouter_api_key),
    "anthropic": make_chat_model(models["anthropic"], OPENROUTER_BASE_URL, openrouter_api_key),
}
