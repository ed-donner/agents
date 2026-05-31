"""
Week 6 MCP server — current date / time tools (Lab 2 exercise pattern).

Run with stdio (used by MCPServerStdio):
  cd 6_mcp && uv run community_contributions/idumachika_week6/date_time_server.py

Or: uv run python community_contributions/idumachika_week6/date_time_server.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date_time_server")


@mcp.tool()
def get_today_iso() -> str:
    """Return today's calendar date as ISO 8601 (YYYY-MM-DD) in UTC."""
    return datetime.now(timezone.utc).date().isoformat()


@mcp.tool()
def get_datetime_iso(timezone_name: str = "UTC") -> str:
    """Return current date and time in ISO format.

    Args:
        timezone_name: IANA zone, e.g. Africa/Lagos, America/New_York, or UTC.
    """
    name = (timezone_name or "UTC").strip()
    if name.upper() == "UTC":
        return datetime.now(timezone.utc).isoformat()
    try:
        tz = ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone: {timezone_name!r}. Use a valid IANA name or UTC."
    return datetime.now(tz).isoformat()


@mcp.resource("datetime://now_utc")
async def now_utc_resource() -> str:
    """Machine-readable current UTC instant."""
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    mcp.run(transport="stdio")
