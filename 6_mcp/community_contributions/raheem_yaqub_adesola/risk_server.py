from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("risk_server")


@mcp.tool()
async def analyze_risk(account: str) -> dict:
    """
    Analyze portfolio risk

    Args:
        account: JSON string of portfolio account
    """

    account_data = json.loads(account)

    holdings = account_data.get("holdings", {})
    total_value = account_data.get("portfolio_value", 0)

    if not holdings:
        return {"risk": "LOW", "message": "No holdings"}

    # simple concentration check
    risks = []

    for symbol, value in holdings.items():
        percentage = value / total_value if total_value else 0

        if percentage > 0.4:
            risks.append(f"{symbol} concentration {percentage:.0%}")

    if risks:
        return {
            "risk": "HIGH",
            "issues": risks,
            "suggestion": "Diversify portfolio",
        }

    return {"risk": "LOW", "message": "Portfolio balanced"}


if __name__ == "__main__":
    mcp.run(transport="stdio")