"""
Lab 2 — Harder exercise: MCP *client* + native OpenAI Chat Completions (no Agents SDK).

Flow (in plain language)
------------------------
1. Start your date MCP server as a child process (stdio).
2. Use the official MCP Python client to connect and list tools.
3. Map those tools into OpenAI's "function calling" JSON shape.
4. Call the OpenAI API. If the model asks to run a tool, you execute it via MCP,
   send the result back to OpenAI, and repeat until the model answers in plain text.

Run (needs OPENAI_API_KEY in the environment, e.g. from .env at repo root)
----------------------------------------------------------------------------
    cd 6_mcp
    uv run community_contributions/manish_tiwari/lab2_solution_harder.py

Or from the repo root:

    uv run 6_mcp/community_contributions/manish_tiwari/lab2_solution_harder.py
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# Load .env from the course repo root (agents/) so OPENAI_API_KEY works like the notebooks.
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

# 6_mcp is two levels up from this file: .../6_mcp/community_contributions/manish_tiwari/
_MCP_DIR = Path(__file__).resolve().parents[2]
_SERVER_SCRIPT = Path("community_contributions/manish_tiwari/lab2_solution_simple.py")


def _mcp_tools_to_openai_functions(tools) -> list[dict]:
    """Turn MCP tool definitions into OpenAI Chat Completions `tools` entries."""
    openai_tools = []
    for tool in tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": (tool.description or "").strip(),
                    "parameters": tool.inputSchema,
                },
            }
        )
    return openai_tools


def _tool_result_text(result) -> str:
    """Extract plain text from an MCP call_tool result."""
    parts = []
    for block in result.content:
        if getattr(block, "text", None):
            parts.append(block.text)
    return "\n".join(parts) if parts else str(result)


async def ask_date_via_mcp_and_openai(user_question: str) -> str:
    server_params = StdioServerParameters(
        command="uv",
        args=["run", str(_SERVER_SCRIPT)],
        cwd=str(_MCP_DIR),
        env={**os.environ},
    )

    client = OpenAI()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            listed = await session.list_tools()
            openai_tools = _mcp_tools_to_openai_functions(listed.tools)

            messages: list[dict] = [{"role": "user", "content": user_question}]
            model = os.environ.get("LAB2_OPENAI_MODEL", "gpt-4.1-mini")

            # Tool loop: keep calling OpenAI until it responds without requesting tools.
            while True:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=openai_tools,
                )
                choice = response.choices[0]
                msg = choice.message

                # No tool calls — we are done.
                if not msg.tool_calls:
                    return (msg.content or "").strip()

                # Record what the assistant said (including tool call requests).
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments or "{}",
                                },
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )

                # Run each requested tool through MCP and append tool results.
                for tc in msg.tool_calls:
                    name = tc.function.name
                    raw_args = tc.function.arguments or "{}"
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}

                    mcp_result = await session.call_tool(name, arguments=args)
                    text_out = _tool_result_text(mcp_result)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": text_out,
                        }
                    )


async def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Add it to your .env at the repo root or export it."
        )

    answer = await ask_date_via_mcp_and_openai(
        "What is today's date? You must use the available tool to get it."
    )
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
