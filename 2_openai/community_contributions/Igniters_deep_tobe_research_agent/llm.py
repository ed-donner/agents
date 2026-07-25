import os

from agents import ModelSettings, OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_SMALL_MODEL = os.getenv(
    "OPENROUTER_SMALL_MODEL",
    os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
)
DEFAULT_LARGE_MODEL = os.getenv(
    "OPENROUTER_LARGE_MODEL",
    os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1"),
)


def _build_default_headers() -> dict[str, str] | None:
    headers: dict[str, str] = {}
    if referer := os.getenv("OPENROUTER_HTTP_REFERER"):
        headers["HTTP-Referer"] = referer
    headers["X-Title"] = os.getenv(
        "OPENROUTER_X_TITLE",
        "Igniters Deep Research Agent",
    )
    return headers or None


def _require_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required to run this project with OpenRouter."
        )
    return api_key


if os.getenv("ENABLE_AGENT_TRACING", "").lower() not in {"1", "true", "yes"}:
    set_tracing_disabled(True)

openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=_require_openrouter_api_key(),
    default_headers=_build_default_headers(),
)

small_model = OpenAIChatCompletionsModel(
    model=DEFAULT_SMALL_MODEL,
    openai_client=openrouter_client,
)
large_model = OpenAIChatCompletionsModel(
    model=DEFAULT_LARGE_MODEL,
    openai_client=openrouter_client,
)

balanced_model_settings = ModelSettings(
    temperature=0.2,
    parallel_tool_calls=True,
)

writer_model_settings = ModelSettings(
    temperature=0.3,
    max_tokens=5000,
)
