"""MCP over SSE: run as a separate process; agent connects via HTTP (remote transport).

Free — no third-party API; listens on 127.0.0.1 by default.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server_remote_sse")

_port = int(os.environ.get("SERVER_MCP_SSE_PORT", "8765"))
mcp.settings.port = _port
mcp.settings.host = os.environ.get("SERVER_MCP_SSE_HOST", "127.0.0.1")


@mcp.tool()
async def remote_utc_now() -> str:
    """Return current UTC time as ISO-8601. Served over the remote (SSE) MCP transport."""
    return f"remote_utc_now: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    # return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@mcp.tool()
async def remote_echo(message: str) -> str:
    """Echo a message back — proves the remote MCP server handled the call.

    Args:
        message: Any short text.
    """
    return f"remote_echo: {message}"


if __name__ == "__main__":
    mcp.run(transport="sse")
