import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Import our consolidated backend logic
from backend import (
    Account, get_share_price, 
    read_risk, write_risk, write_log,
    IS_PAID_POLYGON, IS_REALTIME_POLYGON
)

load_dotenv(override=True)

# Market server
market_mcp = FastMCP("market_server")

class SharePriceArgs(BaseModel):
    symbol: str = Field(description="Stock ticker symbol (e.g. AAPL)")

@market_mcp.tool()
def get_share_price_tool(args: SharePriceArgs) -> float:
    """End-of-day share price as of the prior close (free Polygon tier)."""
    return get_share_price(args.symbol)


# Risk Server
risk_mcp = FastMCP("risk_server")

class NameArgs(BaseModel):
    name: str = Field(description="Trader account name")

class CircuitBreakerArgs(BaseModel):
    name: str = Field(description="Trader account name")
    engaged: bool = Field(description="True to halt trading, False to resume")
    reason: str = Field(description="Reason for the circuit breaker change")

class RiskLimitsArgs(BaseModel):
    name: str = Field(description="Trader account name")
    var_limit: float = Field(description="Max portfolio VaR as fraction of total value (e.g. 0.10 = 10%)")
    max_position_pct: float = Field(description="Max single-position size as fraction of portfolio (e.g. 0.25 = 25%)")
    daily_loss_limit: float = Field(description="Max daily loss as fraction of portfolio before circuit breaker trips (e.g. 0.05 = 5%)")

@risk_mcp.tool()
def get_risk_report(args: NameArgs) -> dict:
    """Assess current risk metrics and circuit breaker status."""
    risk = read_risk(args.name)
    account = Account.get(args.name)
    portfolio_value = account.calculate_portfolio_value()
    
    concentration = {}
    for symbol, qty in account.holdings.items():
        price = get_share_price(symbol)
        position_value = price * qty
        pct = position_value / portfolio_value if portfolio_value > 0 else 0
        concentration[symbol] = round(pct, 4)

    max_concentration = max(concentration.values(), default=0)
    estimated_var = max_concentration * 0.15 # 15% worst-day proxy

    return {
        "name": args.name,
        "circuit_breaker_engaged": risk["circuit_breaker"],
        "limits": {
            "var_limit": risk["var_limit"],
            "max_position_pct": risk["max_position_pct"],
            "daily_loss_limit": risk["daily_loss_limit"],
        },
        "portfolio_value": round(portfolio_value, 2),
        "concentration": concentration,
        "max_concentration": round(max_concentration, 4),
        "estimated_var": round(estimated_var, 4)
    }

@risk_mcp.tool()
def set_circuit_breaker(args: CircuitBreakerArgs) -> str:
    """Engage or disengage the circuit breaker."""
    risk = read_risk(args.name)
    risk["circuit_breaker"] = args.engaged
    write_risk(args.name, risk)
    write_log(args.name, "risk", f"Circuit breaker {'ENGAGED' if args.engaged else 'RELEASED'}: {args.reason}")
    return f"Circuit breaker set to {args.engaged}"

@risk_mcp.tool()
def update_risk_limits(args: RiskLimitsArgs) -> str:
    """Update risk thresholds for a specific trader."""
    risk = read_risk(args.name)
    risk.update({
        "var_limit": args.var_limit,
        "max_position_pct": args.max_position_pct,
        "daily_loss_limit": args.daily_loss_limit
    })
    write_risk(args.name, risk)
    return "Risk limits updated"


# Accounts server
accounts_mcp = FastMCP("accounts_server")

@accounts_mcp.tool()
async def get_balance(name: str) -> float:
    """Get the cash balance of the given account."""
    return Account.get(name).balance

@accounts_mcp.tool()
async def get_holdings(name: str) -> dict[str, int]:
    """Get the holdings of the given account."""
    return Account.get(name).holdings

@accounts_mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Buy shares of a stock."""
    return Account.get(name).buy_shares(symbol, quantity, rationale)

@accounts_mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Sell shares of a stock."""
    return Account.get(name).sell_shares(symbol, quantity, rationale)

@accounts_mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Change investment strategy for the future."""
    return Account.get(name).change_strategy(strategy)

@accounts_mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    return Account.get(name.lower()).report()

@accounts_mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    return Account.get(name.lower()).get_strategy()


# Push Server
push_mcp = FastMCP("push_server")

class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")

@push_mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification via Pushover."""
    user = os.getenv("PUSHOVER_USER")
    token = os.getenv("PUSHOVER_TOKEN")
    if user and token:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "user": user, "token": token, "message": args.message
        })
    return "Push notification sent"


# Rounter / Entry point
if __name__ == "__main__":
    # This allows the same file to be called as different servers
    # based on an argument passed in mcp_params.py
    server_type = sys.argv[1] if len(sys.argv) > 1 else "accounts"
    
    if "market" in server_type:
        market_mcp.run(transport="stdio")
    elif "risk" in server_type:
        risk_mcp.run(transport="stdio")
    elif "push" in server_type:
        push_mcp.run(transport="stdio")
    else:
        accounts_mcp.run(transport="stdio")