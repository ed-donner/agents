"""Input validation for spot crypto simulation."""

from __future__ import annotations

import re
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(override=True)

# Base asset symbols (BTC, ETH, SOL, …) — not full Polygon pairs
_ASSET_RE = re.compile(r"^[A-Z0-9]{2,12}$")

MIN_ORDER_USD = float(os.getenv("MIN_ORDER_USD", "10.0"))
MAX_ORDER_USD = float(os.getenv("MAX_ORDER_USD", "50_000.0"))

MAX_BASE_UNITS = float(os.getenv("MAX_BASE_UNITS", "500.0"))

MAX_TRADES_PER_HOUR = int(os.getenv("MAX_TRADES_PER_HOUR", "120"))


class ValidationError(ValueError):
    """Raised when user or agent input fails validation."""


def normalize_base_asset(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.startswith("X:"):
        body = s[2:]
        if body.endswith("USD"):
            s = body[:-3]
        else:
            raise ValidationError(f"Unsupported pair format: {symbol}")
    if not _ASSET_RE.match(s):
        raise ValidationError(f"Invalid base asset symbol: {symbol}")
    return s


def validate_quantity_base(qty: float, price_usd: float) -> None:
    if qty <= 0:
        raise ValidationError("Quantity must be positive.")
    if qty > MAX_BASE_UNITS:
        raise ValidationError(f"Quantity exceeds per-order cap ({MAX_BASE_UNITS}).")
    notional = qty * price_usd
    if notional < MIN_ORDER_USD:
        raise ValidationError(f"Order below minimum notional (${MIN_ORDER_USD:.2f} USD).")
    if notional > MAX_ORDER_USD:
        raise ValidationError(f"Order above maximum notional (${MAX_ORDER_USD:.2f} USD).")


_trade_timestamps: dict[str, list[float]] = {}


def check_rate_limit(account_name: str) -> None:
    now = datetime.now(timezone.utc).timestamp()
    window = 3600.0
    history = _trade_timestamps.setdefault(account_name.lower(), [])
    history[:] = [t for t in history if now - t < window]
    if len(history) >= MAX_TRADES_PER_HOUR:
        raise ValidationError(
            f"Rate limit: max {MAX_TRADES_PER_HOUR} trades per hour per account."
        )


def record_trade_timestamp(account_name: str) -> None:
    _trade_timestamps.setdefault(account_name.lower(), []).append(
        datetime.now(timezone.utc).timestamp()
    )
