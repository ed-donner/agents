import sys
from pathlib import Path

# Add project root (2 levels up) to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
from mcp.server.fastmcp import FastMCP
from accounts import Account

mcp = FastMCP("Evaluator")

@mcp.tool()
def evaluate_performance(account_name: str) -> str:
    """Evaluate trader's performance with key metrics and recommendations.
    
    Args:
        account_name: The name of the account to evaluate
    """
    account = Account.get(account_name)
    
    # Simple return calculation
    initial_value = 10000  # Starting balance
    current_value = account.total_portfolio_value
    return_percent = ((current_value - initial_value) / initial_value) * 100
    
    # Count positions
    num_positions = len(account.holdings)
    num_trades = len(account.transactions)
    
    # Simple risk check
    if account.holdings and current_value > 0:
        largest_position_value = max(
            (h["quantity"] * h["current_price"] for h in account.holdings.values()),
            default=0
        )
        largest_position_percent = (largest_position_value / current_value) * 100
        risk_level = "High" if largest_position_percent > 50 else "Medium" if largest_position_percent > 30 else "Low"
    else:
        largest_position_percent = 0
        risk_level = "None (no positions)"
    
    # Build simple report
    report = {
        "trader": account_name,
        "performance": {
            "starting_value": initial_value,
            "current_value": round(current_value, 2),
            "return_percent": round(return_percent, 2),
            "profit_loss": round(account.total_profit_loss, 2)
        },
        "portfolio": {
            "cash": round(account.balance, 2),
            "positions": num_positions,
            "holdings": list(account.holdings.keys())
        },
        "activity": {
            "total_trades": num_trades
        },
        "risk": {
            "concentration_risk": risk_level,
            "largest_position_percent": round(largest_position_percent, 2)
        }
    }
    
    return json.dumps(report, indent=2)


if __name__ == "__main__":
    mcp.run()