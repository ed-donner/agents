"""LLM client using OpenRouter (OpenAI-compatible API)."""

from langchain_openai import ChatOpenAI
from config import config


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at OpenRouter."""
    return ChatOpenAI(
        model=config.MODEL,
        temperature=temperature,
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "SideKick",
        },
    )
