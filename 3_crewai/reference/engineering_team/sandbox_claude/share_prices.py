"""Share price lookup module for the trading simulation platform.

Provides fixed share prices for a small set of supported symbols.
"""

from __future__ import annotations

from decimal import Decimal


class UnknownSymbolError(ValueError):
    """Raised when a symbol is not supported by the price lookup."""


class ValidationError(ValueError):
    """Raised when an input value is invalid (e.g. empty symbol)."""


SUPPORTED_SYMBOLS: tuple[str, ...] = ("AAPL", "TSLA", "GOOGL")

FIXED_SHARE_PRICES: dict[str, Decimal] = {
    "AAPL": Decimal("150.00"),
    "TSLA": Decimal("250.00"),
    "GOOGL": Decimal("2800.00"),
}


def normalize_symbol(symbol: str) -> str:
    """Normalize a share symbol by stripping and uppercasing.

    Raises:
        ValidationError: If the symbol is empty or not a string.
    """
    if symbol is None:
        raise ValidationError("Symbol must not be empty.")
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string.")
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValidationError("Symbol must not be empty.")
    return cleaned


def get_share_price(symbol: str) -> Decimal:
    """Return the current fixed price for a supported symbol.

    Raises:
        UnknownSymbolError: If the symbol is not supported.
        ValidationError: If the symbol is empty.
    """
    normalized = normalize_symbol(symbol)
    if normalized not in FIXED_SHARE_PRICES:
        raise UnknownSymbolError(f"Unknown symbol: {normalized}")
    return FIXED_SHARE_PRICES[normalized]
