# healthcheck.py
import asyncio
import os
from dotenv import load_dotenv

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

# Shims
from openai_compat_anthropic import OpenAICompatAnthropicClient
from openai_compat_gemini import GeminiCompatOpenAIClient

load_dotenv(override=True)

# Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Default models (swap with what you actually use in traders.py)
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
GEMINI_MODEL = "gemini-2.5-flash"

def _pretty_msg(resp):
    try:
        msg = resp.choices[0].message
        text = getattr(msg, "content", None)
        if text:
            return text
        # If no content, but tool calls were emitted
        tc = getattr(msg, "tool_calls", None)
        if tc:
            return f"(tool_calls: {len(tc)})"
        # Last resort: whole object
        return str(msg)
    except Exception as e:
        return f"(unreadable message: {e})"

async def check_anthropic():
    print("\n=== Anthropic Health Check ===")
    try:
        anth = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        shim = OpenAICompatAnthropicClient(anth)
        resp = await shim.chat.completions.create(
            model=ANTHROPIC_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1024,
        )
        print("✅ Anthropic shim responded OK")
        print("  Message:", _pretty_msg(resp))
    except Exception as e:
        print("❌ Anthropic check failed:", repr(e))


async def check_gemini():
    print("\n=== Gemini Health Check ===")
    try:
        gemini_raw = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=GOOGLE_API_KEY,
        )
        shim = GeminiCompatOpenAIClient(gemini_raw)
        resp = await shim.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[{"role": "user", "content": "Write one short sentence about the stock market."}],
            max_tokens=1024,
        )
        print("✅ Gemini shim responded OK")
        print("  Message:", _pretty_msg(resp))
    except Exception as e:
        print("❌ Gemini check failed:", repr(e))


async def main():
    await check_anthropic()
    await check_gemini()

if __name__ == "__main__":
    asyncio.run(main())
