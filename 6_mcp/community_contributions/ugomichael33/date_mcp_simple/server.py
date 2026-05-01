from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date_time_server")


@mcp.tool()
def current_datetime() -> str:
    """Return the current date and time in ISO-8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def current_date() -> str:
    """Return today's date in YYYY-MM-DD (UTC)."""
    return datetime.now(timezone.utc).date().isoformat()


if __name__ == "__main__":
    mcp.run(transport="stdio")
