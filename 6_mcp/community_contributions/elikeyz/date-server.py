from mcp.server.fastmcp import FastMCP
from datetime import date

mcp = FastMCP("date_server")

@mcp.tool()
async def current_date() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()

if __name__ == "__main__":
  mcp.run(transport="stdio")
