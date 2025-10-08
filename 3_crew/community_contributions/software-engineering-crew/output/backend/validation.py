from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Optional, Union


Number = Union[Decimal, int, float, str]


class ValidationError(Exception):
    """Base class for validation-related errors."""


class InvalidValueError(ValidationError):
    """Raised when an input value is invalid (type, format, range)."""


class InsufficientFundsError(ValidationError):
    """Raised when cash funds are insufficient for an operation."""


class InsufficientQuantityError(ValidationError):
    """Raised when holdings/quantity are insufficient for an operation."""


@dataclass(frozen=True)
class ValidationRules:
    """
    Centralized business rules to validate amounts, symbols, funds, and quantities.

    This utility provides reusable validation and normalization helpers for:
    - Converting inputs to Decimal with configured precision and rounding.
    - Enforcing positive/non-negative constraints for cash and quantities.
    - Normalizing and validating asset symbols and order sides.
    - Verifying sufficient cash and holdings for operations.
    - Computing quantized totals (quantity * price) using cash precision.

    Notes:
        - Use cash_decimal_places for money values (e.g., 2).
        - Use qty_decimal_places for asset quantities (e.g., 8).
        - Rounding is applied via Decimal.quantize using the configured rounding mode.
    """

    cash_decimal_places: int = 2
    qty_decimal_places: int = 8
    rounding: str = ROUND_HALF_EVEN  # Decimal rounding mode

    def __post_init__(self) -> None:
        if self.cash_decimal_places < 0:
            raise ValueError("cash_decimal_places must be non-negative")
        if self.qty_decimal_places < 0:
            raise ValueError("qty_decimal_places must be non-negative")

        # Derived quantization units
        object.__setattr__(self, "_cash_q", Decimal(10) ** (-self.cash_decimal_places))
        object.__setattr__(self, "_qty_q", Decimal(10) ** (-self.qty_decimal_places))

    # ----------------------------- Converters -----------------------------
    def to_cash(self, value: Number) -> Decimal:
        """Convert a value to a Decimal quantized to cash precision."""
        return self._to_decimal(value, quant=self._cash_q)

    def to_qty(self, value: Number) -> Decimal:
        """Convert a value to a Decimal quantized to quantity precision."""
        return self._to_decimal(value, quant=self._qty_q)

    def require_positive_cash(self, value: Number, *, field: str = "amount") -> Decimal:
        """Convert and ensure a strictly positive cash amount (> 0.00)."""
        dec = self.to_cash(value)
        if dec <= Decimal(0):
            raise InvalidValueError(f"{field} must be greater than zero")
        return dec

    def require_non_negative_cash(self, value: Number, *, field: str = "amount") -> Decimal:
        """Convert and ensure a non-negative cash amount (>= 0.00)."""
        dec = self.to_cash(value)
        if dec < Decimal(0):
            raise InvalidValueError(f"{field} cannot be negative")
        return dec

    def require_positive_qty(self, value: Number, *, field: str = "quantity") -> Decimal:
        """Convert and ensure a strictly positive quantity (> 0)."""
        dec = self.to_qty(value)
        if dec <= Decimal(0):
            raise InvalidValueError(f"{field} must be greater than zero")
        return dec

    def require_non_negative_qty(self, value: Number, *, field: str = "quantity") -> Decimal:
        """Convert and ensure a non-negative quantity (>= 0)."""
        dec = self.to_qty(value)
        if dec < Decimal(0):
            raise InvalidValueError(f"{field} cannot be negative")
        return dec

    # --------------------------- Normalization ---------------------------
    def normalize_symbol(self, symbol: str, *, uppercase: bool = False) -> str:
        """
        Normalize and validate an asset symbol.

        Args:
            symbol: Input symbol value.
            uppercase: If True, returns the symbol in upper case.

        Returns:
            Normalized symbol (stripped; optionally uppercased).

        Raises:
            InvalidValueError: If the symbol is empty or only whitespace.
        """
        sym = (symbol or "").strip()
        if not sym:
            raise InvalidValueError("symbol must be a non-empty string")
        return sym.upper() if uppercase else sym

    def normalize_side(self, side: str) -> str:
        """
        Normalize and validate order side.

        Args:
            side: Input side (e.g., 'buy', 'sell').

        Returns:
            Lowercased side.

        Raises:
            InvalidValueError: If side is not 'buy' or 'sell'.
        """
        s = (side or "").strip().lower()
        if s not in {"buy", "sell"}:
            raise InvalidValueError("side must be 'buy' or 'sell'")
        return s

    # ------------------------ Business Constraints -----------------------
    def ensure_sufficient_funds(
        self,
        available_cash: Number,
        required_cash: Number,
        *,
        field: str = "amount",
    ) -> None:
        """
        Ensure available cash is sufficient for a required amount.

        Args:
            available_cash: Current cash balance.
            required_cash: Cash required for an operation (e.g., total = qty * price).
            field: Name used in error messages.

        Raises:
            InsufficientFundsError: If required_cash exceeds available_cash.
        """
        avail = self.to_cash(available_cash)
        need = self.to_cash(required_cash)
        if need > avail:
            raise InsufficientFundsError(f"Insufficient funds for {field}")

    def ensure_sufficient_quantity(
        self,
        available_qty: Number,
        required_qty: Number,
        *,
        field: str = "quantity",
    ) -> None:
        """
        Ensure available holdings/quantity are sufficient.

        Args:
            available_qty: Current holdings/position.
            required_qty: Quantity required for an operation.
            field: Name used in error messages.

        Raises:
            InsufficientQuantityError: If required_qty exceeds available_qty.
        """
        avail = self.to_qty(available_qty)
        need = self.to_qty(required_qty)
        if need > avail:
            raise InsufficientQuantityError(f"Insufficient {field} available")

    # --------------------------- Calculations ----------------------------
    def total_cash(self, quantity: Number, price: Number) -> Decimal:
        """
        Compute total cash value = quantity * price, quantized to cash precision.

        Args:
            quantity: Trade quantity (qty precision).
            price: Unit price (cash precision).

        Returns:
            Decimal total at cash precision.
        """
        qty = self.to_qty(quantity)
        px = self.to_cash(price)
        return (qty * px).quantize(self._cash_q, rounding=self.rounding)

    # ----------------------------- Internals -----------------------------
    def _to_decimal(self, value: Number, *, quant: Decimal) -> Decimal:
        """Convert a value to Decimal and quantize with configured rounding."""
        try:
            if isinstance(value, Decimal):
                dec = value
            elif isinstance(value, int):
                dec = Decimal(value)
            elif isinstance(value, float):
                # Convert via str to avoid binary floating point surprises
                dec = Decimal(str(value))
            elif isinstance(value, str):
                dec = Decimal(value)
            else:
                raise InvalidValueError(f"unsupported numeric type: {type(value)!r}")
            return dec.quantize(quant, rounding=self.rounding)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidValueError("invalid numeric amount") from exc