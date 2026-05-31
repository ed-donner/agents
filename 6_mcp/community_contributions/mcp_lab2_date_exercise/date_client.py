"""MCP client for date_server: list tools, call tools, map to OpenAI function format."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

EXERCISE_DIR = Path(__file__).resolve().parent
# agents/6_mcp/community_contributions/mcp_lab2_date_exercise -> repo root is 3 parents up
REPO_ROOT = EXERCISE_DIR.parent.parent.parent

params = StdioServerParameters(
    command="uv",
    args=["run", str(EXERCISE_DIR / "date_server.py")],
    cwd=str(REPO_ROOT),
    env=None,
)


async def list_date_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_date_tool(tool_name: str, arguments: dict):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments)


@asynccontextmanager
async def date_server_session():
    """Single long-lived MCP session (useful for OpenAI tool loops)."""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            yield session


def mcp_tools_to_openai_functions(tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI Chat Completions `tools` format."""
    out: list[dict] = []
    for t in tools:
        schema = t.inputSchema if t.inputSchema else {"type": "object", "properties": {}}
        if isinstance(schema, dict) and schema.get("type") is None:
            schema = {"type": "object", **schema}
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": (t.description or "").strip(),
                    "parameters": schema,
                },
            }
        )
    return out


