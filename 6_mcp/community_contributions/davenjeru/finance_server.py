from mcp.server.fastmcp import FastMCP
from finance import FinanceAccount

mcp = FastMCP("finance_server")


@mcp.tool()
async def add_expense(name: str, amount: float, category: str, description: str) -> str:
    """Record a new expense.

    Args:
        name: The account holder's name
        amount: The expense amount (positive number)
        category: Spending category (e.g. Food, Transport, Housing, Entertainment)
        description: What the expense was for
    """
    return FinanceAccount(name).add_expense(amount, category, description)


@mcp.tool()
async def add_income(name: str, amount: float, source: str, description: str) -> str:
    """Record a new income entry.

    Args:
        name: The account holder's name
        amount: The income amount (positive number)
        source: Where the income came from (e.g. Salary, Freelance, Dividends)
        description: Details about the income
    """
    return FinanceAccount(name).add_income(amount, source, description)


@mcp.tool()
async def list_transactions(name: str, category: str = "", month: str = "") -> str:
    """List transactions, optionally filtered by category and/or month.

    Args:
        name: The account holder's name
        category: Filter by category (optional, leave empty for all)
        month: Filter by month in YYYY-MM format (optional, leave empty for all)
    """
    return FinanceAccount(name).list_transactions(category=category, month=month)


@mcp.tool()
async def get_summary(name: str, month: str = "") -> str:
    """Get a financial summary with income, expenses, net, and spending breakdown.

    Args:
        name: The account holder's name
        month: Month in YYYY-MM format (optional, leave empty for all-time summary)
    """
    return FinanceAccount(name).get_summary(month=month)


@mcp.tool()
async def set_budget(name: str, category: str, amount: float) -> str:
    """Set a monthly spending budget for a category.

    Args:
        name: The account holder's name
        category: The spending category to budget
        amount: The monthly budget limit
    """
    return FinanceAccount(name).set_budget(category, amount)


@mcp.resource("finance://summary/{name}")
async def read_summary_resource(name: str) -> str:
    """Read a full financial summary for the given account holder."""
    return FinanceAccount(name).get_summary()


@mcp.resource("finance://budget/{name}")
async def read_budget_resource(name: str) -> str:
    """Read the current budget status for the given account holder."""
    return FinanceAccount(name).budget_status()


if __name__ == "__main__":
    mcp.run(transport="stdio")
