from __future__ import annotations

import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, List, Optional, Union


Number = Union[Decimal, int, float, str]


@dataclass
class Account:
    """Represents a stored account with cash balance and creation timestamp.

    Fields:
        id: Unique account identifier.
        cash_balance: Current cash balance (quantized to cash precision).
        created_at: Account creation timestamp (timezone-aware UTC).
    """

    id: str
    cash_balance: Decimal
    created_at: datetime


@dataclass(frozen=True)
class Transaction:
    """Immutable transaction record persisted by the store.

    Fields:
        timestamp: Creation time of the entry (timezone-aware UTC).
        account_id: Identifier of the account affected.
        type: Transaction type (e.g., 'deposit', 'withdrawal', 'buy', 'sell', 'adjust').
        amount: Cash amount for the transaction (non-negative cash value at cash precision).
        balance_after: Optional cash balance after the transaction.
        symbol: Optional symbol for buy/sell/position adjustments.
        quantity: Optional quantity for symbol-related transactions (qty precision).
        price: Optional unit price for buy/sell transactions (cash precision).
        position_after: Optional position quantity after symbol-related transactions (qty precision).
        memo: Optional free-form note.
    """

    timestamp: datetime
    account_id: str
    type: str
    amount: Decimal
    balance_after: Optional[Decimal]
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    position_after: Optional[Decimal] = None
    memo: Optional[str] = None


class InMemoryStore:
    """In-memory persistence and atomic updates for accounts, holdings, and transactions.

    This storage provides:
      - Creation and management of accounts with cash balances.
      - Per-account holdings storage (symbol -> quantity).
      - Global and per-account immutable transaction logging.
      - Thread-safety and atomic updates via an internal re-entrant lock and an
        `atomic()` context manager for multi-step operations.

    The store performs quantization of cash and quantity values using Decimal with
    configurable precision and rounding. Business validations (e.g., sufficient funds)
    are intentionally minimal so higher-level services can impose domain-specific rules.
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

        self._accounts: Dict[str, Account] = {}
        self._holdings: Dict[str, Dict[str, Decimal]] = {}
        self._transactions: List[Transaction] = []
        self._per_account_tx: Dict[str, List[Transaction]] = {}
        self._lock = threading.RLock()

    # ---------------------------- Account APIs ----------------------------
    def create_account(self, account_id: Optional[str] = None, *, initial_cash: Number = 0) -> str:
        """Create a new account with an optional initial cash balance.

        Args:
            account_id: Optional explicit account identifier. If None, a UUID4 hex is generated.
            initial_cash: Initial cash balance (quantized to cash precision). Must be non-negative.

        Returns:
            The created account identifier.

        Raises:
            ValueError: If the account already exists or initial_cash is negative/invalid.
        """
        with self._lock:
            aid = account_id or uuid.uuid4().hex
            if aid in self._accounts:
                raise ValueError(f"Account '{aid}' already exists")

            cash = self._to_cash(initial_cash)
            if cash < Decimal(0):
                raise ValueError("initial_cash cannot be negative")

            now = datetime.now(timezone.utc)
            self._accounts[aid] = Account(id=aid, cash_balance=cash, created_at=now)
            self._holdings[aid] = {}
            self._per_account_tx[aid] = []
            return aid

    def list_accounts(self) -> List[str]:
        """Return a list of all account IDs."""
        with self._lock:
            return list(self._accounts.keys())

    def get_account(self, account_id: str) -> Account:
        """Return a snapshot of the account.

        Raises:
            KeyError: If the account does not exist.
        """
        with self._lock:
            acct = self._get_account(account_id)
            # Return a defensive copy to avoid external mutation of internal state
            return Account(id=acct.id, cash_balance=acct.cash_balance, created_at=acct.created_at)

    def get_cash_balance(self, account_id: str) -> Decimal:
        """Return the current cash balance for the account.

        Raises:
            KeyError: If the account does not exist.
        """
        with self._lock:
            return self._get_account(account_id).cash_balance

    def set_cash_balance(self, account_id: str, new_balance: Number) -> Decimal:
        """Set the cash balance for an account to a specific value (quantized).

        Returns the new balance.

        Raises:
            KeyError: If the account does not exist.
            ValueError: If new_balance cannot be converted to a valid cash amount.
        """
        with self._lock:
            acct = self._get_account(account_id)
            acct.cash_balance = self._to_cash(new_balance)
            return acct.cash_balance

    def adjust_cash(self, account_id: str, delta: Number) -> Decimal:
        """Adjust the cash balance by a delta (can be positive or negative).

        Returns the new balance.

        Raises:
            KeyError: If the account does not exist.
            ValueError: If delta cannot be converted to a valid cash amount.
        """
        with self._lock:
            acct = self._get_account(account_id)
            new_bal = (acct.cash_balance + self._to_cash(delta)).quantize(self._cash_q, rounding=self._rounding)
            acct.cash_balance = new_bal
            return new_bal

    # ---------------------------- Holdings APIs ---------------------------
    def get_positions(self, account_id: str) -> Dict[str, Decimal]:
        """Return a shallow copy of symbol -> quantity positions for the account.

        Raises:
            KeyError: If the account does not exist.
        """
        with self._lock:
            self._ensure_account_exists(account_id)
            return dict(self._holdings.get(account_id, {}))

    def get_position(self, account_id: str, symbol: str) -> Decimal:
        """Return the position size for a symbol (zero if none).

        Raises:
            KeyError: If the account does not exist.
        """
        with self._lock:
            self._ensure_account_exists(account_id)
            sym = self._normalize_symbol(symbol)
            return self._holdings[account_id].get(sym, Decimal(0))

    def set_position(self, account_id: str, symbol: str, quantity: Number) -> Decimal:
        """Set the position for a symbol to an exact quantity (quantized).

        Quantity of zero removes the symbol from holdings. Returns the new position quantity.

        Raises:
            KeyError: If the account does not exist.
            ValueError: If the quantity cannot be converted to a valid number.
        """
        with self._lock:
            self._ensure_account_exists(account_id)
            sym = self._normalize_symbol(symbol)
            qty = self._to_qty(quantity)
            if qty == Decimal(0):
                self._holdings[account_id].pop(sym, None)
                return Decimal(0)
            self._holdings[account_id][sym] = qty
            return qty

    def adjust_position(self, account_id: str, symbol: str, delta: Number) -> Decimal:
        """Adjust the position for a symbol by delta (can be positive or negative).

        If the resulting position is zero, the symbol is removed from holdings.
        Returns the new position quantity.

        Raises:
            KeyError: If the account does not exist.
            ValueError: If the delta cannot be converted to a valid number.
        """
        with self._lock:
            self._ensure_account_exists(account_id)
            sym = self._normalize_symbol(symbol)
            curr = self._holdings[account_id].get(sym, Decimal(0))
            new_qty = (curr + self._to_qty(delta)).quantize(self._qty_q, rounding=self._rounding)
            if new_qty == Decimal(0):
                self._holdings[account_id].pop(sym, None)
                return Decimal(0)
            self._holdings[account_id][sym] = new_qty
            return new_qty

    # --------------------------- Transactions APIs ------------------------
    def record_transaction(
        self,
        *,
        account_id: str,
        type: str,
        amount: Number,
        symbol: Optional[str] = None,
        quantity: Optional[Number] = None,
        price: Optional[Number] = None,
        balance_after: Optional[Number] = None,
        position_after: Optional[Number] = None,
        memo: Optional[str] = None,
    ) -> Transaction:
        """Record a transaction entry for an account.

        Notes:
            - `type` is stored verbatim (after stripping/lowercasing); callers can use any label
              such as 'deposit', 'withdrawal', 'buy', 'sell', or domain-specific tags.
            - Monetary and quantity fields are quantized to the store's configured precision.

        Raises:
            KeyError: If the account does not exist.
            ValueError: If numeric fields cannot be converted to Decimal.
        """
        with self._lock:
            self._ensure_account_exists(account_id)
            t_type = (type or "").strip().lower()
            sym = self._normalize_symbol(symbol) if symbol is not None else None

            amt = self._to_cash(amount)
            qty = self._to_qty(quantity) if quantity is not None else None
            px = self._to_cash(price) if price is not None else None
            bal_after = self._to_cash(balance_after) if balance_after is not None else None
            pos_after = self._to_qty(position_after) if position_after is not None else None

            entry = Transaction(
                timestamp=datetime.now(timezone.utc),
                account_id=account_id,
                type=t_type,
                amount=amt,
                balance_after=bal_after,
                symbol=sym,
                quantity=qty,
                price=px,
                position_after=pos_after,
                memo=memo,
            )
            self._log_transaction(entry)
            return entry

    def get_transactions(self, account_id: Optional[str] = None) -> List[Transaction]:
        """Retrieve transactions (global or per-account).

        Args:
            account_id: If provided, returns only transactions for that account.

        Returns:
            A new list of Transaction instances in chronological order.
        """
        with self._lock:
            if account_id is None:
                return list(self._transactions)
            return list(self._per_account_tx.get(account_id, []))

    # --------------------------- Atomic operations ------------------------
    @contextmanager
    def atomic(self):
        """Context manager for atomic multi-step updates.

        Usage:
            with store.atomic():
                store.adjust_cash(aid, 10)
                store.adjust_position(aid, "ABC", 1)
                store.record_transaction(account_id=aid, type="deposit", amount=10, balance_after=store.get_cash_balance(aid))
        """
        self._lock.acquire()
        try:
            yield self
        finally:
            self._lock.release()

    def apply(self, func):
        """Execute a callable under the store lock and return its result.

        This is a convenience for atomic read-modify-write operations.
        """
        with self._lock:
            return func(self)

    # ------------------------------ Internals -----------------------------
    def _get_account(self, account_id: str) -> Account:
        acct = self._accounts.get(account_id)
        if acct is None:
            raise KeyError(f"Account '{account_id}' not found")
        return acct

    def _ensure_account_exists(self, account_id: str) -> None:
        if account_id not in self._accounts:
            raise KeyError(f"Account '{account_id}' not found")

    def _log_transaction(self, entry: Transaction) -> None:
        self._transactions.append(entry)
        self._per_account_tx.setdefault(entry.account_id, []).append(entry)

    def _normalize_symbol(self, symbol: str) -> str:
        s = (symbol or "").strip()
        if not s:
            raise ValueError("symbol must be a non-empty string")
        return s

    # Converters
    def _to_cash(self, value: Number) -> Decimal:
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
                raise ValueError(f"unsupported cash type: {type(value)!r}")
            return dec.quantize(self._cash_q, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid cash amount") from exc

    def _to_qty(self, value: Number) -> Decimal:
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
                raise ValueError(f"unsupported quantity type: {type(value)!r}")
            return dec.quantize(self._qty_q, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid quantity amount") from exc