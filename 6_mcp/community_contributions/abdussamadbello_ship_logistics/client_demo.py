"""
Minimal stdio MCP client: list tools and call one sample tool.
Run from anywhere with: python client_demo.py
(requires cwd-compatible imports — run from this directory or set PYTHONPATH).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

_ROOT = Path(__file__).resolve().parent
_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[str(_ROOT / "server.py")],
    cwd=str(_ROOT),
    env=None,
)


def _tool_result_to_text(result) -> str:
    parts = getattr(result, "content", None) or getattr(result, "contents", None) or []
    out = []
    for c in parts:
        t = getattr(c, "text", None)
        if t is not None:
            out.append(t)
        else:
            out.append(str(c))
    return "\n".join(out) if out else str(result)


async def list_tools():
    async with stdio_client(_PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return (await session.list_tools()).tools


async def call_tool(name: str, arguments: dict | None = None):
    async with stdio_client(_PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return await session.call_tool(name, arguments or {})


async def main() -> None:
    tools = await list_tools()
    print("Tools:", [t.name for t in tools])
    res = await call_tool(
        "corridor_summary",
        {"origin_port_id": "SGSIN", "dest_port_id": "NLRTM"},
    )
    text = _tool_result_to_text(res)
    try:
        data = json.loads(text)
        print("Sample corridor_summary (pretty):")
        print(json.dumps(data, indent=2)[:2000])
    except json.JSONDecodeError:
        print("Sample corridor_summary (raw):")
        print(text[:2000])


if __name__ == "__main__":
    asyncio.run(main())
