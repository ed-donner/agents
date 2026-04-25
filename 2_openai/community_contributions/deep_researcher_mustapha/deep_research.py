"""
deep_research.py — Shared OpenRouter client configuration.
All agents import `setup_client()` from here.
"""
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv

# Ensure we find the .env file in the parent directory if not in the current one
load_dotenv(find_dotenv())

# ── Constants ───────────────────────────────────────────────────────────────
BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model aliases
MODEL_FAST = "google/gemini-2.0-flash-001"           # planner + search
MODEL_CAPABLE = "openai/gpt-4o-mini"                 # writer + email
MODEL_GUARD = "google/gemini-2.0-flash-001"           # security analyst

# litellm-prefixed versions for agents that use hosted models via litellm
LITELLM_FAST = f"litellm/openrouter/{MODEL_FAST}"


def setup_client():
    """
    Creates and registers the AsyncOpenAI client pointed at OpenRouter
    as the global default for the OpenAI Agents SDK.
    """
    from agents import (
        set_default_openai_api,
        set_default_openai_client,
        set_tracing_export_api_key,
    )

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found. Please check your .env file.")

    client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=BASE_URL)
    set_default_openai_api("chat_completions")
    set_default_openai_client(client)

    if OPENAI_API_KEY:
        set_tracing_export_api_key(OPENAI_API_KEY)

    return client
