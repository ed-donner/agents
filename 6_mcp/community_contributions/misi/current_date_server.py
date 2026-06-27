from mcp.server.fastmcp import FastMCP
from datetime import date

mcp = FastMCP("current_date_server")


@mcp.tool()
async def get_current_date() -> str:
    """Get the current date in YYYY-MM-DD format."""
    return date.today().strftime("%Y-%m-%d")


if __name__ == "__main__":
    mcp.run(transport="stdio")
