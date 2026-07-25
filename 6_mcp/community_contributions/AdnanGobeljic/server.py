from mcp.server.fastmcp import FastMCP
import beans

mcp = FastMCP("coffee_roastery")


@mcp.tool()
def list_beans() -> list[str]:
    """All available green bean origin codes."""

    return beans.list_beans()


@mcp.tool()
def get_bean(code: str) -> dict:
    """Info on a bean origin"""

    return beans.get_bean(code)


@mcp.tool()
def list_roast_levels() -> list[str]:
    """Available roast levels"""

    return beans.list_roast_levels()


@mcp.tool()
def get_roast_profile(level: str) -> dict:
    """Temp and timing for a given roast level."""

    return beans.get_roast_profile(level)


@mcp.tool()
def flavor_notes(bean_code: str, roast_level: str) -> dict:
    """Expected tasting notes for a bean at a given roast."""

    return beans.flavor_notes(bean_code, roast_level)


@mcp.tool()
def brew_recipe(method: str) -> dict:
    """Ratio, grind, temp and time for a brew method."""

    return beans.brew_recipe(method)


@mcp.tool()
def batch_cost(bean_code: str, green_kg: float) -> dict:
    """Rough cost breakdown for roasting a batch of green beans."""

    return beans.batch_cost(bean_code, green_kg)


@mcp.tool()
def recommend(bean_code: str, roast_level: str, method: str) -> dict:
    """All-in-one: bean info + roast profile + flavors + brew params."""
    
    return beans.recommend(bean_code, roast_level, method)


if __name__ == "__main__":
    mcp.run(transport="stdio")
