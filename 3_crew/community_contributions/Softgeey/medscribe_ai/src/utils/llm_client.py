"""Thin OpenRouter API client used by all agents."""

import json
import requests
from src.config import get_openrouter_key, get_model

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 120  # seconds


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """
    Send a chat completion request to OpenRouter.
    Returns the assistant message text.
    Raises on HTTP errors or missing content.
    """
    headers = {
        "Authorization": f"Bearer {get_openrouter_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://medscribe-ai.local",
        "X-Title": "MedScribe AI",
    }

    payload = {
        "model": get_model(),
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=TIMEOUT)
    response.raise_for_status()

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected OpenRouter response structure: {data}") from e
