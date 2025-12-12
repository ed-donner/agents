"""
server.py - MCP Server for Shopping List

This wraps the ShoppingList class as MCP tools that can be
called by clients (including LLM-powered agents).

Run with: uv run server.py
"""
from mcp.server.fastmcp import FastMCP
from shopping_list import get_shopping_list
from typing import Optional

mcp = FastMCP("shopping_list_server")

@mcp.tool()
async def add_item(name: str, quantity: int = 1, category: str = "General", price: Optional[float] = None) -> dict:
    """Add an item to the shopping list.
    If the item already exists, the quantity will be increased.

    Args:
        name: Name of the item to add (e.g., "Milk", "Bread")
        quantity: Number of items to add (default: 1)
        category: Category like Produce, Dairy, Bakery, Pantry, Frozen, Snacks (default: General)
        price: Price per item in dollars (optional, for budget tracking)
    Returns:
        A dictionary with success status, action (add or update), message, and item details.
    """
    return get_shopping_list().add_item(name, quantity, category, price)

@mcp.tool()
async def remove_item(name: str) -> dict:
    """Remove an item from the shopping list.
    If the item does not exist, the function will return a failure message.

    Args:
        name: Name of the item to remove (e.g., "Milk", "Bread")
    Returns:
        A dictionary with success status and message.
    """
    return get_shopping_list().remove_item(name)

@mcp.tool()
async def get_list() -> dict:
    """Get the current shopping list.
    Returns:
        A dictionary with success status, list of items, total items, total cost, budget, and remaining budget.
    """
    return get_shopping_list().get_list()

@mcp.tool()
async def set_budget(amount: float) -> dict:
    """Set the shopping budget.
    Args:
        amount: The new budget amount in dollars
    Returns:
        A dictionary with success status, message, and new budget.
    """
    return get_shopping_list().set_budget(amount)

@mcp.tool()
async def get_budget_status() -> dict:
    """Get the current budget status.
    Returns:
        A dictionary with success status, total cost, budget, remaining budget, percentage used, and status.
        The status is a string with the following indicators:
        - 🟢 On track (under 80% of budget)
        - 🟡 Warning (80-100% of budget)
        - 🔴 Over budget
    """
    return get_shopping_list().get_budget_status()

@mcp.tool()
async def clear_list() -> dict:
    """Clear the shopping list.
    Returns:
        A dictionary with success status and message.
    """
    return get_shopping_list().clear_list()

if __name__ == "__main__":
    mcp.run(transport="stdio")