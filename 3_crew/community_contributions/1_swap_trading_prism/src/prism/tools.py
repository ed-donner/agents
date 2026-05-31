# src/prism/tools.py
"""All tools for PRISM trading system."""
from datetime import datetime

from crewai.tools import tool
from pydantic import Field

from .database import DatabaseConnection


# ============================================================================
# Calculation Tools
# ============================================================================

def _calculate_years_to_maturity_internal(maturity_date):
    """Calculate years to maturity."""
    if isinstance(maturity_date, str):
        maturity = datetime.strptime(maturity_date, "%Y-%m-%d")
    else:
        maturity = maturity_date

    today = datetime.now()
    days_remaining = (maturity - today).days
    years = days_remaining / 365.25
    return max(years, 0)


def _calculate_swap_pnl_internal(position, current_rate):
    """Calculate swap P&L (for testing)."""
    entry_rate = float(position["fixed_rate"])
    notional = float(position["notional"])
    years_to_maturity = _calculate_years_to_maturity_internal(position["maturity_date"])
    dv01 = notional * 0.0001 * years_to_maturity
    rate_change_bps = (current_rate - entry_rate) * 10000

    # For RCV_FIXED: profit when rates decrease (entry_rate > current_rate)
    # For PAY_FIXED: profit when rates increase (current_rate > entry_rate)
    if position["pay_receive"] == "RCV_FIXED":
        pnl = (
            -rate_change_bps * dv01
        )  # Negative of rate change (profit when rates drop)
    else:  # PAY_FIXED
        pnl = rate_change_bps * dv01  # Positive rate change (profit when rates rise)

    return {
        "position_id": position["position_id"],
        "entry_rate": entry_rate,
        "current_rate": current_rate,
        "rate_change_bps": round(rate_change_bps, 2),
        "pnl": round(pnl, 2),
        "notional": notional,
    }


def _check_trading_signal_internal(pnl, threshold_profit=50000, threshold_loss=-25000):
    """Check trading signal (for testing)."""
    if pnl >= threshold_profit:
        return {
            "signal": "CLOSE",
            "reason": f"Profit target hit: ${pnl:,.2f} >= ${threshold_profit:,.2f}",
            "action": "Close position to lock in profit",
        }
    elif pnl <= threshold_loss:
        return {
            "signal": "CLOSE",
            "reason": f"Stop loss hit: ${pnl:,.2f} <= ${threshold_loss:,.2f}",
            "action": "Close position to limit loss",
        }
    else:
        return {
            "signal": "HOLD",
            "reason": f"P&L ${pnl:,.2f} within acceptable range",
            "action": "Continue monitoring",
        }


def _calculate_dynamic_thresholds_internal(position, volatility=0.02):
    """Calculate dynamic thresholds (for testing)."""
    notional = float(position["notional"])
    if notional >= 20000000:
        profit_pct = 0.003
        loss_pct = 0.0015
    elif notional >= 10000000:
        profit_pct = 0.005
        loss_pct = 0.0025
    else:
        profit_pct = 0.01
        loss_pct = 0.005

    profit_target = notional * profit_pct * (1 + volatility * 10)
    stop_loss = -notional * loss_pct * (1 + volatility * 10)

    return {
        "position_id": position["position_id"],
        "profit_target": round(profit_target, 2),
        "stop_loss": round(stop_loss, 2),
    }


@tool("Calculate Swap PnL")
def calculate_swap_pnl(
    position: dict = Field(  # noqa: B008
        ...,
        description="Position dictionary with keys: position_id, fixed_rate, notional, pay_receive, maturity_date",
    ),
    current_rate: float = Field(  # noqa: B008
        ..., description="Current market swap rate as decimal (e.g., 0.0435 for 4.35%)"
    ),
):
    """Calculate the P&L for a swap position.

    Formula: (Current_Rate - Entry_Rate) × Notional × Years × Direction
    """
    result = _calculate_swap_pnl_internal(position, current_rate)
    return result


@tool("Calculate Years to Maturity")
def calculate_years_to_maturity(
    maturity_date: str = Field(
        ..., description="Maturity date in YYYY-MM-DD format (e.g., '2029-01-15')"
    ),
):
    """Calculate years remaining until swap maturity."""
    years = _calculate_years_to_maturity_internal(maturity_date)
    return years


@tool("Check Trading Signal")
def check_trading_signal(
    pnl: float = Field(..., description="Current P&L in dollars"),
    threshold_profit: float = Field(
        default=50000, description="Profit target in dollars"
    ),
    threshold_loss: float = Field(default=-25000, description="Stop loss in dollars"),
):
    """Determine if a trading signal should be triggered based on P&L thresholds."""
    signal = _check_trading_signal_internal(pnl, threshold_profit, threshold_loss)
    return signal


@tool("Calculate Dynamic Thresholds")
def calculate_dynamic_thresholds(
    position: dict = Field(..., description="Position with notional and maturity"),  # noqa: B008
    volatility: float = Field(default=0.02, description="Recent rate volatility"),  # noqa: B008
):
    """Calculate dynamic profit/loss thresholds based on position size and volatility."""
    return _calculate_dynamic_thresholds_internal(position, volatility)


# ============================================================================
# Database Tools
# ============================================================================

@tool("Get All Positions")
def get_all_positions():
    """Fetch all trader swap positions from database."""
    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT position_id, trade_date, maturity_date, notional,
               fixed_rate, float_index, pay_receive, currency
        FROM swap_positions
        ORDER BY trade_date DESC
    """

    positions = db.execute_query(query)
    db.close()

    return positions


@tool("Get Position By ID")
def get_position_by_id(position_id: str):
    """Fetch a specific swap position by ID."""
    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT * FROM swap_positions WHERE position_id = ?
    """

    position = db.execute_query(query, (position_id,))
    db.close()

    return position[0] if position else None


@tool("Insert Trade Signal")
def insert_trade_signal(
    position_id: str,
    signal_type: str,
    current_pnl: float,
    reason: str,
    recommended_action: str,
):
    """Insert a trade signal into the database."""
    db = DatabaseConnection()
    db.connect()

    insert_query = """
        INSERT INTO trade_signals (position_id, signal_type, current_pnl, reason, recommended_action, timestamp, executed)
        VALUES (?, ?, ?, ?, ?, datetime('now'), 0)
    """

    db.execute_query(
        insert_query,
        (position_id, signal_type, current_pnl, reason, recommended_action),
    )
    db.close()

    return f"Signal {signal_type} recorded for {position_id}"


# ============================================================================
# Market Data Tools
# ============================================================================

@tool("Store Market Rates")
def store_market_rates(rates: list):
    """Store market rates in database."""
    db = DatabaseConnection()
    db.connect()

    for rate in rates:
        # Strip % and convert to float if needed
        mid_rate = rate["mid_rate"]
        if isinstance(mid_rate, str):
            mid_rate = float(mid_rate.replace("%", ""))

        # Same for bid_rate and ask_rate
        bid_rate = rate.get("bid_rate", mid_rate - 0.01)
        if isinstance(bid_rate, str):
            bid_rate = float(bid_rate.replace("%", ""))

        ask_rate = rate.get("ask_rate", mid_rate + 0.01)
        if isinstance(ask_rate, str):
            ask_rate = float(ask_rate.replace("%", ""))

        insert_query = """
            INSERT INTO market_rates (tenor, currency, mid_rate, bid_rate, ask_rate, timestamp, source)
            VALUES (?, ?, ?, ?, ?, datetime('now'), 'Serper')
        """
        db.execute_query(
            insert_query,
            (rate["tenor"], rate.get("currency", "USD"), mid_rate, bid_rate, ask_rate),
        )

    db.close()
    return f"Stored {len(rates)} rates"


@tool("Get Latest Market Rate")
def get_latest_market_rate(tenor: str, currency: str = "USD"):
    """Get the most recent market rate for a specific tenor."""
    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT mid_rate, bid_rate, ask_rate, timestamp
        FROM market_rates
        WHERE tenor = ? AND currency = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """

    result = db.execute_query(query, (tenor, currency))
    db.close()

    return result[0] if result else None
