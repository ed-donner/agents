from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date_time_server")

@mcp.tool()
async def get_current_date() -> str:
    """Return today's date in ISO format (UTC)."""
    return datetime.now(timezone.utc).date().isoformat()

@mcp.tool()
async def get_current_datetime() -> str:
    """Return current date-time in ISO format (UTC)."""
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    mcp.run(transport="stdio")
