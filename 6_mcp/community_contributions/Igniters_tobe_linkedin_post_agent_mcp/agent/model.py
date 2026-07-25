from __future__ import annotations

from functools import lru_cache

from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from config.settings import get_settings


@lru_cache(maxsize=1)
def get_model():
    settings = get_settings()
    settings.validate_openrouter()
    extra_headers = {}
    if settings.openrouter_http_referer:
        extra_headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_title:
        extra_headers["X-Title"] = settings.openrouter_title
    client = AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        default_headers=extra_headers or None,
    )
    return OpenAIChatCompletionsModel(model=settings.openrouter_model, openai_client=client)
