from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("date_server")

@mcp.tool()
async def current_date() -> str:
    """Return today's date and time in ISO format (YYYY-MM-DD)."""
    return datetime.today().isoformat()

if __name__ == "__main__":
  mcp.run(transport="stdio")
