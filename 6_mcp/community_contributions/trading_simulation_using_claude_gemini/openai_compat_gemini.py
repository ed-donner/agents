# openai_compat_gemini.py
import asyncio
import random
from typing import Any, Dict

# ---------------------------
# Retry helper (exponential)
# ---------------------------
async def _with_retries(
    fn, *args, retries: int = 3, base_delay: float = 0.6, jitter: float = 0.5, **kwargs
):
    attempt = 0
    while True:
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt > retries:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            delay = delay * (1 + jitter * random.random())
            print(f"[WARN] Gemini attempt {attempt} failed: {e}. Retrying in {delay:.2f}s…")
            await asyncio.sleep(delay)


# Keys that commonly cause Gemini's OpenAI-compat endpoint to 500
_UNSUPPORTED = {
    "parallel_tool_calls",
    "reasoning_effort",
    "store",
    "stream_options",
}


def _is_given(v: Any) -> bool:
    if v is None:
        return False
    return v.__class__.__name__ != "NotGiven"


def _clean_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(kwargs)

    # Drop unsupported keys
    for k in list(out.keys()):
        if k in _UNSUPPORTED:
            out.pop(k, None)

    # Tool choice sanity
    tc = out.get("tool_choice")
    if tc not in (None, "auto", "none", "required"):
        out["tool_choice"] = "auto"

    # response_format sanity
    rf = out.get("response_format")
    if isinstance(rf, dict):
        t = rf.get("type")
        if t not in (None, "text"):
            out["response_format"] = {"type": "text"}

    # Reasonable defaults if caller omitted
    if not _is_given(out.get("max_tokens")):
        out["max_tokens"] = 1024
    if not _is_given(out.get("temperature")):
        out["temperature"] = 0.3

    return out


class _ChatCompletionsProxy:
    def __init__(self, underlying_chat_completions, retry_fn=None):
        self._u = underlying_chat_completions
        self._retry = retry_fn or _with_retries

    async def create(self, **kwargs):
        cleaned = _clean_kwargs(kwargs)
        return await self._retry(self._u.create, **cleaned)


class _ChatProxy:
    def __init__(self, underlying_chat, retry_fn=None):
        self.completions = _ChatCompletionsProxy(underlying_chat.completions, retry_fn=retry_fn)


class GeminiCompatOpenAIClient:
    """
    Wraps openai.AsyncOpenAI to sanitize requests for Google's OpenAI-compat endpoint:
      - strips unsupported kwargs (prevents 500 errors)
      - adds mild retry
      - preserves .api_key and .base_url for SDK inspection
    """
    def __init__(self, openai_client, retry_fn=None):
        self._u = openai_client
        self.api_key = getattr(openai_client, "api_key", None)
        self.base_url = getattr(openai_client, "base_url", None)
        self.chat = _ChatProxy(openai_client.chat, retry_fn=retry_fn)
        # Pass-through if your SDK uses responses API too
        self.responses = getattr(openai_client, "responses", None)

    def __getattr__(self, item):
        return getattr(self._u, item)
