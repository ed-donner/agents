# test_claude_tools_minimal.py
import asyncio
import os
from anthropic import AsyncAnthropic
from openai_compat_anthropic import OpenAICompatAnthropicClient
from dotenv import load_dotenv

load_dotenv(override=True)  # <-- ensure ANTHROPIC_API_KEY is loaded

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-3-7-sonnet-20250219?maxtok=2048&temp=0.5" # or "claude-3-7-sonnet-latest"

async def main():
    anth = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    shim = OpenAICompatAnthropicClient(anth)

    # Minimal fake tool similar to your market MCP shape
    tools = [
        {
            "type": "function",
            "function": {
                "name": "lookup_share_price",
                "description": "Get last closing price for a stock symbol.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker, e.g. AAPL"},
                    },
                    "required": ["symbol"],
                },
            },
        }
    ]

    messages = [
        {"role": "system", "content": "You can call tools to look up data."},
        {"role": "user", "content": "Use the tool to get AAPL price."},
    ]

    # Call through the OpenAI-compatible chat.completions path
    resp = await shim.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        max_tokens=300,
        temperature=0,
    )

    print("type(resp):", type(resp))
    print("choices[0].message:", resp.choices[0].message.model_dump())

    # If the conversion worked, you should see tool_calls in the message
    tc = getattr(resp.choices[0].message, "tool_calls", None)
    print("tool_calls:", tc)

asyncio.run(main())
