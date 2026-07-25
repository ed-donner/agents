from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math_server")

@mcp.tool()
async def add(x: int, y: int) -> int:
    """
    Takes two numbers, adds them and returns the result of the addition
    Args:
        x: An integer
        y: An integer
    """
    return x + y



@mcp.tool()
def sub(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the subtraction(x-y)
    Args:
        x: An integer
        y: An integer
    """
    return x - y



@mcp.tool()
def div(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the division(x/y)
    Args:
        x: An integer
        y: An integer
    """
    return x / y



@mcp.tool()
def mul(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the multiplication(x*y)
    Args:
        x: An integer
        y: An integer
    """
    return x * y


@mcp.resource("resource://jokes")
def math_joke()->str:
    """
    Returns a math joke of the day
    """

    return "Archimedes was killed while solving math"


if __name__ == "__main__":
    mcp.run(transport="stdio")