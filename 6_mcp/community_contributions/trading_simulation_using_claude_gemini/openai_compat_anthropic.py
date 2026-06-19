# openai_compat_anthropic.py
import time
import asyncio
import random
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Union, Optional

# Anthropic async client (pip install anthropic)
from anthropic import AsyncAnthropic

# OpenAI types, used to return real ChatCompletion objects
# (install openai >= 1.40)
from openai.types.chat.chat_completion import ChatCompletion, Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from openai.types.completion_usage import CompletionUsage

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
            print(f"[WARN] Anthropic attempt {attempt} failed: {e}. Retrying in {delay:.2f}s…")
            await asyncio.sleep(delay)


# ---------------------------
# Helpers
# ---------------------------
def _is_given(v: Any) -> bool:
    if v is None:
        return False
    # avoid importing NotGiven; check by class name
    return v.__class__.__name__ != "NotGiven"


def _convert_openai_tools_to_anthropic(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Convert OpenAI function tools to Anthropic tool schema.
    OpenAI tool:
      {"type":"function", "function":{"name":..., "description":..., "parameters":{...}}}
    Anthropic tool:
      {"name":..., "description":..., "input_schema": {...}}
    """
    if not tools:
        return []
    converted: List[Dict[str, Any]] = []
    for t in tools:
        if t.get("type") == "function" and isinstance(t.get("function"), dict):
            fn = t["function"]
            converted.append(
                {
                    "name": fn.get("name", "tool"),
                    "description": fn.get("description") or "",
                    "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
                }
            )
    return converted


def _convert_openai_messages_to_anthropic(
    messages: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Convert OpenAI-style messages into Anthropic’s format and return:
      (system_prompt: str, conv: List[{"role": "...", "content": ...}])

    Also:
    - Skips truly empty text messages (Anthropic validation requires non-empty content)
    - Converts OpenAI tool calls and tool results into Anthropic tool blocks
    """
    system_prompt = ""
    if messages and messages[0].get("role") == "system":
        system_prompt = messages[0].get("content") or ""
        messages = messages[1:]

    conv: List[Dict[str, Any]] = []

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content")

        # Handle TOOL RESULT messages (role == "tool")
        if role == "tool":
            tool_use_id = m.get("tool_call_id") or m.get("tool_use_id") or ""
            tool_text = "" if content is None else str(content)
            if tool_text.strip() == "":
                tool_text = "OK"
            blocks = [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": tool_text,
            }]
            conv.append({"role": "user", "content": blocks})
            continue

        # Handle assistant tool calls (OpenAI style):
        tool_calls = m.get("tool_calls")
        if role == "assistant" and tool_calls:
            blocks: List[Dict[str, Any]] = []
            # include assistant text if present
            text = "" if content is None else str(content)
            if text.strip():
                blocks.append({"type": "text", "text": text})
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "tool")
                args = fn.get("arguments", "{}")
                blocks.append({
                    "type": "tool_use",
                    "id": call.get("id", ""),
                    "name": name,
                    "input": _safe_parse_json(args),
                })
            if blocks:
                conv.append({"role": "assistant", "content": blocks})
            # If blocks were somehow empty, skip to avoid empty message
            continue

        # Default text messages
        text = "" if content is None else str(content)
        if text.strip() == "":
            # Skip empty messages (Anthropic requirement)
            continue
        # Anthropic only knows "user" and "assistant" roles for messages
        anth_role = role if role in ("user", "assistant") else "user"
        conv.append({"role": anth_role, "content": text})

    return system_prompt, conv


def _safe_parse_json(s: Any) -> Any:
    try:
        import json
        if isinstance(s, str):
            return json.loads(s)
    except Exception:
        pass
    return s


def _anthropic_to_openai_choice(anth_msg: Any) -> ChatCompletionChoice:
    """
    Convert Anthropic's Message object into an OpenAI ChatCompletionChoice with tool calls if present.
    """
    text_out = ""
    tool_calls: List[ChatCompletionMessageToolCall] = []

    content = getattr(anth_msg, "content", None)
    if isinstance(content, list):
        for block in content:
            btype = getattr(block, "type", None) or (isinstance(block, dict) and block.get("type"))
            if btype == "text":
                # SDK block: block.text ; dict block: block["text"]
                txt = getattr(block, "text", None) or (isinstance(block, dict) and block.get("text")) or ""
                text_out += txt
            elif btype == "tool_use":
                tool_id = getattr(block, "id", None) or (isinstance(block, dict) and block.get("id")) or ""
                name = getattr(block, "name", None) or (isinstance(block, dict) and block.get("name")) or "tool"
                input_obj = getattr(block, "input", None) or (isinstance(block, dict) and block.get("input")) or {}
                import json
                tool_calls.append(
                    ChatCompletionMessageToolCall(
                        id=tool_id or f"toolu_{int(time.time())}",
                        type="function",
                        function=Function(name=name, arguments=json.dumps(input_obj)),
                    )
                )

    message = ChatCompletionMessage(role="assistant", content=text_out or "", tool_calls=tool_calls)

    # usage safe defaults
    usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
    return choice


# ---------------------------
# Shims
# ---------------------------
class _ResponsesShim:
    """Implements client.responses.create(...), returns real OpenAI ChatCompletion."""
    def __init__(self, anthropic_client: AsyncAnthropic, retry_fn=None):
        self._anth = anthropic_client
        self._retry = retry_fn or _with_retries

    async def create(self, **kwargs):
        # Normalize core args and Claude-safe defaults
        model: str = kwargs.get("model")

        # Defaults unless caller provided values
        max_tokens = kwargs.get("max_output_tokens")
        if not _is_given(max_tokens):
            max_tokens = kwargs.get("max_tokens")
        if not _is_given(max_tokens):
            max_tokens = 1024

        temperature = kwargs.get("temperature")
        if not _is_given(temperature):
            temperature = 0.3

        top_p = kwargs.get("top_p")
        if not _is_given(top_p):
            top_p = 0.9

        # Tools (OpenAI -> Anthropic)
        openai_tools = kwargs.get("tools")
        anth_tools = _convert_openai_tools_to_anthropic(openai_tools)
        tools_kw = {"tools": anth_tools} if anth_tools else {}

        # Messages or input
        messages = kwargs.get("messages")
        if messages is None or not _is_given(messages):
            inp = kwargs.get("input")
            if isinstance(inp, list):
                messages = inp
            elif isinstance(inp, str):
                messages = [{"role": "user", "content": inp}]
            else:
                messages = [{"role": "user", "content": str(inp)}]

        system_prompt, conv = _convert_openai_messages_to_anthropic(messages)

        # Optional params
        anth_kwargs: Dict[str, Any] = {"temperature": temperature, "top_p": top_p}
        for k in ("top_k", "metadata"):
            v = kwargs.get(k)
            if _is_given(v):
                anth_kwargs[k] = v

        stop = kwargs.get("stop")
        if _is_given(stop):
            anth_kwargs["stop_sequences"] = stop if isinstance(stop, list) else [stop]

        explicit_system = kwargs.get("system")
        if _is_given(explicit_system):
            system_to_send = explicit_system
        else:
            system_to_send = system_prompt

        # Call Anthropic with retries
        anth_resp = await self._retry(
            self._anth.messages.create,
            model=model,
            max_tokens=max_tokens,
            system=system_to_send,
            messages=conv,
            **tools_kw,
            **anth_kwargs,
        )

        # Convert Anthropic message to OpenAI ChatCompletion
        choice = _anthropic_to_openai_choice(anth_resp)

        chat_completion = ChatCompletion.model_validate({
            "id": f"anthropic-shim-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [choice],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        })
        return chat_completion


class _ChatCompletionsShim:
    """Implements client.chat.completions.create(...)."""
    def __init__(self, responses_shim: _ResponsesShim):
        self._responses = responses_shim

    async def create(self, **kwargs):
        return await self._responses.create(**kwargs)


class _ChatShim:
    """Provides .completions shim as client.chat.completions."""
    def __init__(self, responses_shim: _ResponsesShim):
        self.completions = _ChatCompletionsShim(responses_shim)


class OpenAICompatAnthropicClient:
    """
    Duck-types minimal openai.AsyncOpenAI client for Anthropic:
      - .api_key (str)
      - .base_url (str)
      - .responses.create(...)
      - .chat.completions.create(...)
    """
    def __init__(self, anthropic_client: AsyncAnthropic, retry_fn=None):
        self._anthropic = anthropic_client
        self.api_key = getattr(anthropic_client, "api_key", None)
        self.base_url = "https://api.anthropic.com/v1"

        self._responses = _ResponsesShim(anthropic_client, retry_fn=retry_fn)
        self.responses = self._responses
        self.chat = _ChatShim(self._responses)

    # pass-through for anything else your SDK might touch
    def __getattr__(self, item):
        return getattr(self._anthropic, item)
