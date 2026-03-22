"""OpenRouter vs OpenAI model routing for the Agents SDK."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv(override=True)

OPENROUTER_MODEL = "openai/gpt-4o-mini"
OPENAI_MODEL = "gpt-4o-mini"

if os.getenv("OPENROUTER_API_KEY"):
    key = os.getenv("OPENROUTER_API_KEY", "")
    os.environ["OPENAI_API_KEY"] = key
    base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    os.environ["OPENAI_BASE_URL"] = base
    set_tracing_disabled(True)
    _client = AsyncOpenAI(base_url=base, api_key=key)
    AGENT_MODEL: OpenAIChatCompletionsModel | str = OpenAIChatCompletionsModel(
        model=OPENROUTER_MODEL,
        openai_client=_client,
    )
else:
    AGENT_MODEL = OPENAI_MODEL
