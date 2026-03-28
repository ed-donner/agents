from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("sport_server")

class SportModelArgs(BaseModel):
    sport: str = Field(description="The sport to get information about")

@mcp.tool()
def get_sport_info(sport: SportModelArgs) -> str:
    """
    Get information about a sport
    Args:
        sport: The sport to get information about
    Returns:
        A string with the information about the sport
    """
    return f"The information about {sport.sport }"

if __name__ == "__main__":
   mcp.run(transport='stdio')
