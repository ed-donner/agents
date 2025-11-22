# src/prism/tools/calculation_tools.py
from datetime import datetime

from crewai.tools import tool
from pydantic import Field

from ..utils import logger


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
    position_id = position.get("position_id", "unknown")
    logger.info(f"💰 Calculating P&L for position {position_id}")

    result = _calculate_swap_pnl_internal(position, current_rate)
    logger.info(
        f"  P&L: ${result['pnl']:,.2f} | Rate change: {result['rate_change_bps']} bps"
    )
    return result


@tool("Calculate Years to Maturity")
def calculate_years_to_maturity(
    maturity_date: str = Field(
        ..., description="Maturity date in YYYY-MM-DD format (e.g., '2029-01-15')"
    ),
):
    """Calculate years remaining until swap maturity."""
    years = _calculate_years_to_maturity_internal(maturity_date)
    logger.debug(f"  Years to maturity: {years:.2f} (maturity: {maturity_date})")
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
    logger.debug(
        f"🔍 Checking trading signal: P&L=${pnl:,.2f}, Profit threshold=${threshold_profit:,.2f}, Loss threshold=${threshold_loss:,.2f}"
    )

    signal = _check_trading_signal_internal(pnl, threshold_profit, threshold_loss)

    if signal["signal"] == "CLOSE":
        logger.warning(f"🚨 {signal['signal']}: {signal['reason']}")
    else:
        logger.debug(f"  Signal: {signal['signal']} - {signal['reason']}")

    return signal


@tool("Calculate Dynamic Thresholds")
def calculate_dynamic_thresholds(
    position: dict = Field(..., description="Position with notional and maturity"),  # noqa: B008
    volatility: float = Field(default=0.02, description="Recent rate volatility"),  # noqa: B008
):
    """Calculate dynamic profit/loss thresholds based on position size and volatility."""
    return _calculate_dynamic_thresholds_internal(position, volatility)
