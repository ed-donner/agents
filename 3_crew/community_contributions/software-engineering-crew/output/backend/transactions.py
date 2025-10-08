from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, List, Optional, Union
import threading


class InvalidTransactionError(Exception):
    """Raised when a transaction has invalid parameters."""


@dataclass(frozen=True)
class TransactionEntry:
    """Immutable record of an account transaction.

    Fields:
        timestamp: Creation time of the entry (timezone-aware UTC).
        account_id: Identifier of the account affected.
        type: Transaction type: 'deposit', 'withdrawal', 'buy', or 'sell'.
        amount: Positive cash amount for the transaction. For buys/sells, this is total = quantity * price.
        balance_after: Optional cash balance after the transaction.
        symbol: Optional symbol for buy/sell transactions.
        quantity: Optional quantity for buy/sell transactions.
        price: Optional unit price for buy/sell transactions.
        position_after: Optional position quantity (for the symbol) after buy/sell.
        memo: Optional free-form note.
    """

    timestamp: datetime
    account_id: str
    type: str  # 'deposit', 'withdrawal', 'buy', 'sell'
    amount: Decimal
    balance_after: Optional[Decimal]
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    position_after: Optional[Decimal] = None
    memo: Optional[str] = None


class TransactionLedger:
    """In-memory ledger to persist and retrieve account transactions.

    - Records deposits, withdrawals, and buy/sell trades as immutable entries.
    - Uses Decimal for monetary and quantity values with configurable precision.
    - Thread-safe for concurrent operations within a single process.

    This class does not enforce account existence or balance logic; callers
    are expected to supply valid values (e.g., resulting balances/positions).
    """

    def __init__(
        self,
        cash_decimal_places: int = 2,
        qty_decimal_places: int = 8,
        rounding=ROUND_HALF_EVEN,
    ) -> None:
        if cash_decimal_places < 0:
            raise ValueError("cash_decimal_places must be non-negative")
        if qty_decimal_places < 0:
            raise ValueError("qty_decimal_places must be non-negative")

        self._cash_q: Decimal = Decimal(10) ** (-cash_decimal_places)
        self._qty_q: Decimal = Decimal(10) ** (-qty_decimal_places)
        self._rounding = rounding

        self._entries: List[TransactionEntry] = []
        self._per_account: Dict[str, List[TransactionEntry]] = {}
        self._lock = threading.RLock()

    # ---------------------------- Public API ----------------------------
    def record_deposit(
        self,
        account_id: str,
        amount: Union[Decimal, int, float, str],
        *,
        balance_after: Optional[Union[Decimal, int, float, str]] = None,
        memo: Optional[str] = None,
    ) -> TransactionEntry:
        """Record a deposit transaction.

        Args:
            account_id: Account identifier.
            amount: Positive deposit amount.
            balance_after: Optional resulting cash balance after the deposit.
            memo: Optional note to store on the entry.

        Returns:
            The created TransactionEntry.

        Raises:
            InvalidTransactionError: If amount is invalid or not strictly positive.
        """
        with self._lock:
            dec_amount = self._to_decimal(amount, quant=self._cash_q)
            if dec_amount <= Decimal(0):
                raise InvalidTransactionError("deposit amount must be greater than zero")

            bal_after = self._to_optional_decimal(balance_after, quant=self._cash_q)
            entry = TransactionEntry(
                timestamp=datetime.now(timezone.utc),
                account_id=account_id,
                type="deposit",
                amount=dec_amount,
                balance_after=bal_after,
                memo=memo,
            )
            self._log(entry)
            return entry

    def record_withdrawal(
        self,
        account_id: str,
        amount: Union[Decimal, int, float, str],
        *,
        balance_after: Optional[Union[Decimal, int, float, str]] = None,
        memo: Optional[str] = None,
    ) -> TransactionEntry:
        """Record a withdrawal transaction.

        Args:
            account_id: Account identifier.
            amount: Positive withdrawal amount.
            balance_after: Optional resulting cash balance after the withdrawal.
            memo: Optional note to store on the entry.

        Returns:
            The created TransactionEntry.

        Raises:
            InvalidTransactionError: If amount is invalid or not strictly positive.
        """
        with self._lock:
            dec_amount = self._to_decimal(amount, quant=self._cash_q)
            if dec_amount <= Decimal(0):
                raise InvalidTransactionError("withdrawal amount must be greater than zero")

            bal_after = self._to_optional_decimal(balance_after, quant=self._cash_q)
            entry = TransactionEntry(
                timestamp=datetime.now(timezone.utc),
                account_id=account_id,
                type="withdrawal",
                amount=dec_amount,
                balance_after=bal_after,
                memo=memo,
            )
            self._log(entry)
            return entry

    def record_buy(
        self,
        account_id: str,
        symbol: str,
        quantity: Union[Decimal, int, float, str],
        price: Union[Decimal, int, float, str],
        *,
        cash_balance_after: Optional[Union[Decimal, int, float, str]] = None,
        position_after: Optional[Union[Decimal, int, float, str]] = None,
        memo: Optional[str] = None,
    ) -> TransactionEntry:
        """Record a buy trade transaction.

        Args:
            account_id: Account identifier.
            symbol: Asset symbol (non-empty string).
            quantity: Quantity to buy (must be > 0), quantized to qty precision.
            price: Unit price (must be > 0), quantized to cash precision.
            cash_balance_after: Optional cash balance after the trade.
            position_after: Optional position size for the symbol after the trade.
            memo: Optional note to store on the entry.

        Returns:
            The created TransactionEntry.

        Raises:
            InvalidTransactionError: If parameters are invalid.
        """
        return self._record_trade(
            account_id=account_id,
            side="buy",
            symbol=symbol,
            quantity=quantity,
            price=price,
            cash_balance_after=cash_balance_after,
            position_after=position_after,
            memo=memo,
        )

    def record_sell(
        self,
        account_id: str,
        symbol: str,
        quantity: Union[Decimal, int, float, str],
        price: Union[Decimal, int, float, str],
        *,
        cash_balance_after: Optional[Union[Decimal, int, float, str]] = None,
        position_after: Optional[Union[Decimal, int, float, str]] = None,
        memo: Optional[str] = None,
    ) -> TransactionEntry:
        """Record a sell trade transaction.

        Args:
            account_id: Account identifier.
            symbol: Asset symbol (non-empty string).
            quantity: Quantity to sell (must be > 0), quantized to qty precision.
            price: Unit price (must be > 0), quantized to cash precision.
            cash_balance_after: Optional cash balance after the trade.
            position_after: Optional position size for the symbol after the trade.
            memo: Optional note to store on the entry.

        Returns:
            The created TransactionEntry.

        Raises:
            InvalidTransactionError: If parameters are invalid.
        """
        return self._record_trade(
            account_id=account_id,
            side="sell",
            symbol=symbol,
            quantity=quantity,
            price=price,
            cash_balance_after=cash_balance_after,
            position_after=position_after,
            memo=memo,
        )

    def get_transactions(self, account_id: Optional[str] = None) -> List[TransactionEntry]:
        """Retrieve transactions, either globally or for a specific account.

        Args:
            account_id: If provided, returns only transactions for that account.

        Returns:
            A new list of TransactionEntry instances in chronological order.
        """
        with self._lock:
            if account_id is None:
                return list(self._entries)
            return list(self._per_account.get(account_id, []))

    # --------------------------- Internal Utils ---------------------------
    def _record_trade(
        self,
        *,
        account_id: str,
        side: str,
        symbol: str,
        quantity: Union[Decimal, int, float, str],
        price: Union[Decimal, int, float, str],
        cash_balance_after: Optional[Union[Decimal, int, float, str]],
        position_after: Optional[Union[Decimal, int, float, str]],
        memo: Optional[str],
    ) -> TransactionEntry:
        norm_side = (side or "").strip().lower()
        if norm_side not in {"buy", "sell"}:
            raise InvalidTransactionError("side must be 'buy' or 'sell'")

        sym = (symbol or "").strip()
        if not sym:
            raise InvalidTransactionError("symbol must be a non-empty string")

        qty = self._to_decimal(quantity, quant=self._qty_q)
        px = self._to_decimal(price, quant=self._cash_q)

        if qty <= Decimal(0):
            raise InvalidTransactionError("quantity must be greater than zero")
        if px <= Decimal(0):
            raise InvalidTransactionError("price must be greater than zero")

        total = (qty * px).quantize(self._cash_q, rounding=self._rounding)

        bal_after = self._to_optional_decimal(cash_balance_after, quant=self._cash_q)
        pos_after = self._to_optional_decimal(position_after, quant=self._qty_q)

        entry = TransactionEntry(
            timestamp=datetime.now(timezone.utc),
            account_id=account_id,
            type=norm_side,
            amount=total,
            balance_after=bal_after,
            symbol=sym,
            quantity=qty,
            price=px,
            position_after=pos_after,
            memo=memo,
        )
        with self._lock:
            self._log(entry)
            return entry

    def _to_decimal(self, value: Union[Decimal, int, float, str], *, quant: Decimal) -> Decimal:
        """Convert a value to a quantized Decimal with configured rounding."""
        try:
            if isinstance(value, Decimal):
                dec = value
            elif isinstance(value, int):
                dec = Decimal(value)
            elif isinstance(value, float):
                dec = Decimal(str(value))
            elif isinstance(value, str):
                dec = Decimal(value)
            else:
                raise InvalidTransactionError(f"unsupported numeric type: {type(value)!r}")
            return dec.quantize(quant, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidTransactionError("invalid numeric amount") from exc

    def _to_optional_decimal(
        self, value: Optional[Union[Decimal, int, float, str]], *, quant: Decimal
    ) -> Optional[Decimal]:
        if value is None:
            return None
        return self._to_decimal(value, quant=quant)

    def _log(self, entry: TransactionEntry) -> None:
        self._entries.append(entry)
        self._per_account.setdefault(entry.account_id, []).append(entry)