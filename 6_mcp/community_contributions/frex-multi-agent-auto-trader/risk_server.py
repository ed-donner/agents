"""
risk_server.py — FastMCP server exposing Risk Manager tools.

Tools consumed by the Execution Trader (circuit breaker gate) and
by the Risk Manager Agent (monitoring & control).
"""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from database import read_risk, write_risk, write_log
from accounts import Account
from market import get_share_price
from datetime import datetime

mcp = FastMCP("risk_server")


# Pydantic arg models

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

class RiskEventArgs(BaseModel):
    name: str = Field(description="Trader account name")
    event: str = Field(description="Description of the risk event observed")
    severity: str = Field(description="low | medium | high | critical")


# Tools 

@mcp.tool()
def check_circuit_breaker(args: NameArgs) -> dict:
    """Check whether trading is currently halted for this account.
    The Execution Trader MUST call this before placing any order.
    Returns {'engaged': bool, 'reason': str | None}.
    """
    risk = read_risk(args.name)
    events = risk.get("events", [])
    last_reason = events[-1]["event"] if events else None
    return {
        "engaged": risk["circuit_breaker"],
        "reason": last_reason if risk["circuit_breaker"] else None,
    }


@mcp.tool()
def set_circuit_breaker(args: CircuitBreakerArgs) -> str:
    """Engage or disengage the trading circuit breaker for an account.
    Only the Risk Manager should call this tool.
    """
    risk = read_risk(args.name)
    risk["circuit_breaker"] = args.engaged
    events = risk.get("events", [])
    events.append({
        "timestamp": datetime.now().isoformat(),
        "event": f"Circuit breaker {'ENGAGED' if args.engaged else 'DISENGAGED'}: {args.reason}",
        "severity": "critical" if args.engaged else "medium",
    })
    risk["events"] = events[-50:]  # keep last 50
    write_risk(args.name, risk)
    status = "ENGAGED — trading halted" if args.engaged else "DISENGAGED — trading resumed"
    write_log(args.name, "risk", f"Circuit breaker {status}: {args.reason}")
    return f"Circuit breaker {status}."


@mcp.tool()
def set_risk_limits(args: RiskLimitsArgs) -> str:
    """Update the risk limits for an account (VaR, position size, daily loss).
    Only the Risk Manager should call this tool.
    """
    risk = read_risk(args.name)
    risk["var_limit"] = args.var_limit
    risk["max_position_pct"] = args.max_position_pct
    risk["daily_loss_limit"] = args.daily_loss_limit
    write_risk(args.name, risk)
    write_log(args.name, "risk", f"Limits updated: VaR={args.var_limit:.0%}, pos={args.max_position_pct:.0%}, loss={args.daily_loss_limit:.0%}")
    return f"Risk limits updated for {args.name}."


@mcp.tool()
def log_risk_event(args: RiskEventArgs) -> str:
    """Log an observed risk event (concentration, volatility spike, correlation break, etc.).
    The Risk Manager calls this to maintain an audit trail.
    """
    risk = read_risk(args.name)
    events = risk.get("events", [])
    events.append({
        "timestamp": datetime.now().isoformat(),
        "event": args.event,
        "severity": args.severity,
    })
    risk["events"] = events[-50:]
    write_risk(args.name, risk)
    write_log(args.name, "risk", f"[{args.severity.upper()}] {args.event}")
    return f"Risk event logged."


@mcp.tool()
def get_risk_report(args: NameArgs) -> dict:
    """Return the full risk profile for an account: limits, circuit breaker status,
    computed concentration risk, estimated VaR, and recent events.
    """
    risk = read_risk(args.name)
    account = Account.get(args.name)
    portfolio_value = account.calculate_portfolio_value()

    # Concentration risk — largest single position as % of portfolio
    concentration = {}
    for symbol, qty in account.holdings.items():
        price = get_share_price(symbol)
        position_value = price * qty
        pct = position_value / portfolio_value if portfolio_value > 0 else 0
        concentration[symbol] = round(pct, 4)

    max_concentration = max(concentration.values(), default=0)

    # Simple historical VaR proxy: sum of position sizes weighted equally 
    estimated_var = max_concentration * 0.15  # assume 15% worst-day move on top position

    breaches = []
    if max_concentration > risk["max_position_pct"]:
        breaches.append(f"Position concentration breach: {max_concentration:.0%} > {risk['max_position_pct']:.0%} limit")
    if estimated_var > risk["var_limit"]:
        breaches.append(f"VaR breach: estimated {estimated_var:.0%} > {risk['var_limit']:.0%} limit")

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
        "estimated_var": round(estimated_var, 4),
        "breaches": breaches,
        "recent_events": risk["events"][-10:],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
