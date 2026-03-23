"""
Provider configuration — edit this file to switch between OpenAI, Groq, or OpenRouter.

Set PROVIDER to one of: "openai" | "groq" | "openrouter"

IMPORTANT: Groq does NOT support the json_schema response format that the Agents SDK
uses for structured outputs (output_type on agents). Use openrouter or openai instead.
Groq works fine for simple text agents but breaks agents that return Pydantic models.

Default is openrouter — it supports json_schema and the user's OPENROUTER_API_KEY works.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import OpenAIChatCompletionsModel, set_default_openai_api, set_default_openai_client, set_tracing_disabled

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Change this line to switch provider
# ---------------------------------------------------------------------------
PROVIDER = os.environ.get("RESEARCH_PROVIDER", "openrouter")  # openrouter | openai | groq*
# *Groq does not support json_schema structured outputs — use openrouter or openai

# ---------------------------------------------------------------------------
# Provider-specific model and client settings
# ---------------------------------------------------------------------------
_PROVIDERS = {
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
    },
    "openrouter": {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
}

_cfg = _PROVIDERS.get(PROVIDER, _PROVIDERS["groq"])

# ---------------------------------------------------------------------------
# Configure the Agents SDK to use the chosen provider
# ---------------------------------------------------------------------------
_client = AsyncOpenAI(
    api_key=os.environ.get(_cfg["api_key_env"], ""),
    base_url=_cfg["base_url"],
)

set_default_openai_api("chat_completions")   # required for non-OpenAI providers
set_default_openai_client(_client)

# Use OpenAIChatCompletionsModel directly instead of a model name string.
# This bypasses the SDK's prefix router (which rejects "meta-llama/..." etc.)
# and ties the model explicitly to the configured client — same pattern as lab 2.
DEFAULT_MODEL = OpenAIChatCompletionsModel(
    model=_cfg["model"],
    openai_client=_client,
)

# Tracing sends data to OpenAI's platform — disable it when not using OpenAI
# to avoid the [non-fatal] 401 warning on every run.
if PROVIDER != "openai":
    set_tracing_disabled(True)

print(f"[config] Provider: {PROVIDER} | Model: {_cfg['model']}")
