"""MCP server: exposes today's date as a tool (Week 6 Lab 2 exercise)."""

from datetime import date

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date_server")


@mcp.tool()
async def get_current_date() -> str:
    """Return today's calendar date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


if __name__ == "__main__":
    mcp.run(transport="stdio")
