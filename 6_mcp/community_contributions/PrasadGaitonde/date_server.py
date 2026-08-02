from mcp.server.fastmcp import FastMCP
from datetime import date

mcp = FastMCP("date_server")

@mcp.tool()
async def get_current_date() -> str:
    """Return the current date.
    """
    return str(date.today())

if __name__ == "__main__":
    mcp.run(transport='stdio')
