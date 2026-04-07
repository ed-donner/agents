"""Shared RunConfig for OpenAI-compatible APIs (OpenAI, OpenRouter, etc.)."""

from __future__ import annotations

import os

from agents import OpenAIProvider, RunConfig
from dotenv import load_dotenv

load_dotenv(override=True)


def get_run_config() -> RunConfig:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
    if not base_url:
        base_url = None
    if not base_url and os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        base_url = "https://openrouter.ai/api/v1"
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return RunConfig(model_provider=provider)
