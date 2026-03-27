from mcp.server.fastmcp import FastMCP
from groceries import Grocery

mcp = FastMCP("smartfridge_server")

@mcp.tool()
async def stock(name: str, quantity: int):
    """Stock grocery item given the name and quantity.

    Args:
        name: The name of the grocery
        quantity: the amount of the grocery
    """
    Grocery.get_or_create(name).stock(quantity)


@mcp.tool()
async def consume(name: str, quantity: int):
    """Consume grocery item given the name and quantity.

    Args:
        name: The name of the grocery
        quantity: the amount of the grocery
    """
    return Grocery.get_or_create(name).consume(quantity)


@mcp.tool()
async def list_transactions(name: str):
    """List all transactions for a grocery item.

    Args:
        name: The name of the grocery
    """
    return Grocery.get_or_create(name).list_transactions()


@mcp.resource("groceries://smartfridge_server/{name}")
async def get_grocery_report(name: str) -> str:
    grocery = Grocery.get(name.lower())
    if grocery is None:
        return f"Grocery item '{name}' not found."
    return grocery.get_grocery_report()


if __name__ == "__main__":
    mcp.run(transport='stdio')