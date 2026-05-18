"""Async MCP stdio client for courtroom tools."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_MCP_ROOT = Path(__file__).resolve().parent.parent
_SERVER_SCRIPT = _MCP_ROOT / "mcp_server" / "server.py"


def _clean_env() -> dict[str, str]:
    return {k: str(v) for k, v in os.environ.items() if v is not None}


def mcp_result_to_text(result) -> str:
    """Flatten MCP CallToolResult content to plain text."""
    parts: list[str] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


@asynccontextmanager
async def courtroom_mcp_session():
    """Spawn courtroom MCP server (stdio) and yield a connected ClientSession."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-u", str(_SERVER_SCRIPT)],
        cwd=str(_MCP_ROOT),
        env=_clean_env(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
