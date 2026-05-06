from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("date_server")

@mcp.tool()
async def get_date() -> str:
    """Get the current date and time.

    Args:
        None
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
async def write_a_song() -> str:
    return "some bullshit song!"
if __name__ == "__main__":
    mcp.run(transport='stdio')

