

from __future__ import annotations

import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

load_dotenv(override=True)
set_tracing_disabled(True)


def _groq_model() -> OpenAIChatCompletionsModel:
    key = os.getenv("GROQ_API_KEY")
    if not key or not key.strip():
        raise SystemExit(
            "Missing GROQ_API_KEY. Set it in your environment or .env file "
            "(https://console.groq.com/keys)."
        )
    model_id = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=key.strip())
    return OpenAIChatCompletionsModel(model=model_id, openai_client=client)


async def main() -> None:
    here = Path(__file__).resolve().parent
    rates_params = {"command": "uv", "args": ["run", str(here / "rates_server.py")]}
    convert_params = {"command": "uv", "args": ["run", str(here / "convert_server.py")]}

    instructions = """You are a foreign exchange assistant with access to two MCP tool servers.

Use the tools (do not guess exchange rates):
- get_latest_rates: arguments base (ISO currency, e.g. USD), symbols (comma-separated quotes, e.g. EUR,GBP).
- convert_amount: arguments amount (number), from_currency, to_currency (ISO codes), optional date (YYYY-MM-DD) for historical conversion.

Call tools as needed to answer the user. Summarize results clearly."""

    prompt = os.getenv(
        "FOREX_AGENT_PROMPT",
        "What are the latest USD exchange rates for EUR and GBP? Then convert 250 USD to EUR.",
    )

    model = _groq_model()

    async with AsyncExitStack() as stack:
        rates_mcp = await stack.enter_async_context(
            MCPServerStdio(params=rates_params, client_session_timeout_seconds=120)
        )
        convert_mcp = await stack.enter_async_context(
            MCPServerStdio(params=convert_params, client_session_timeout_seconds=120)
        )
        agent = Agent(
            name="forex_groq_agent",
            instructions=instructions,
            model=model,
            mcp_servers=[rates_mcp, convert_mcp],
        )
        result = await Runner.run(agent, prompt)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
