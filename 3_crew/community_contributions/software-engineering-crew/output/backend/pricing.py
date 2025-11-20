from __future__ import annotations

from decimal import Decimal


class PricingService:
    """
    Simple pricing service that returns fixed test share prices.

    This service exposes get_share_price(symbol) and provides fixed prices for:
    - AAPL
    - TSLA
    - GOOGL

    Prices are returned as Decimal values suitable for financial calculations.
    """

    def __init__(self) -> None:
        # Fixed test prices; extend as needed for additional symbols.
        self._prices = {
            "AAPL": Decimal("190.00"),
            "TSLA": Decimal("250.00"),
            "GOOGL": Decimal("140.00"),
        }

    def get_share_price(self, symbol: str) -> Decimal:
        """
        Return the share price for the given symbol.

        Args:
            symbol: Stock ticker symbol (case-insensitive; e.g., 'AAPL').

        Returns:
            Decimal price for the symbol.

        Raises:
            ValueError: If symbol is an empty string or only whitespace.
            KeyError: If the symbol does not have a configured price.
        """
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol must be a non-empty string")

        try:
            return self._prices[sym]
        except KeyError as exc:
            raise KeyError(f"Price for symbol '{sym}' not available") from exc