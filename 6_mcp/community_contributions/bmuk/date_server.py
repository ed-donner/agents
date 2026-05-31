from mcp.server.fastmcp import FastMCP
from date_picker import get_date, get_date_with_timezone

mcp = FastMCP("date_server")

@mcp.tool()
async def get_current_date_with_timezone(timezone: str) -> str:
    """Get the current date and time in the specified timezone.

    Args:
        timezone: The timezone to get the date for (e.g., "US/Eastern", "Europe/London", "Asia/Tokyo")
    """
    return get_date_with_timezone(timezone)

@mcp.tool()
async def get_current_date() -> str:
    """Get the current date and time in the server's local timezone."""
    return get_date()

if __name__ == "__main__":
    mcp.run(transport="stdio")