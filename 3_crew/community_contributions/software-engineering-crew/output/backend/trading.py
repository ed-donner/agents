from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, List, Optional, Union
import threading
import uuid


class TradingError(Exception):
    """Base class for trading-related errors."""


class AccountNotFoundError(TradingError):
    """Raised when an account does not exist in the trading engine."""


class AccountAlreadyExistsError(TradingError):
    """Raised when an account with the given ID already exists."""


class InvalidOrderError(TradingError):
    """Raised when an order has invalid parameters (e.g., non-positive quantity or price)."""


class InsufficientCashError(TradingError):
    """Raised when there is not enough cash to execute a buy order."""


class InsufficientHoldingsError(TradingError):
    """Raised when there are not enough holdings to execute a sell order."""


@dataclass
class AccountPortfolio:
    """Represents an account portfolio containing cash and a creation timestamp."""

    id: str
    cash_balance: Decimal
    created_at: datetime


@dataclass(frozen=True)
class TradeRecord:
    """Immutable trade record for a buy or sell execution."""

    timestamp: datetime
    account_id: str
    side: str  # 'buy' or 'sell'
    symbol: str
    quantity: Decimal
    price: Decimal
    total: Decimal  # money value of the trade; non-negative
    cash_balance_after: Decimal
    position_after: Decimal  # position for the traded symbol after execution
    memo: Optional[str] = None


class TradingEngine:
    """
    Trading engine that executes buy/sell orders, validates operations,
    updates cash balances and holdings, and records immutable trade entries.

    - Uses Decimal for monetary and quantity values with configurable precision.
    - Thread-safe for concurrent operations within a single process.
    - Maintains global and per-account trade ledgers.
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

        self._accounts: Dict[str, AccountPortfolio] = {}
        self._holdings: Dict[str, Dict[str, Decimal]] = {}
        self._trades: List[TradeRecord] = []
        self._per_account_trades: Dict[str, List[TradeRecord]] = {}
        self._lock = threading.RLock()

    # ---------------------------- Public API ----------------------------
    def create_account(
        self,
        account_id: Optional[str] = None,
        initial_cash: Union[Decimal, int, float, str] = 0,
    ) -> str:
        """
        Create a new trading account with an optional initial cash balance.

        Args:
            account_id: Optional explicit account identifier. If None, a UUID4 hex is generated.
            initial_cash: Non-negative initial cash balance.

        Returns:
            The account identifier.

        Raises:
            AccountAlreadyExistsError: If the specified account_id already exists.
            InvalidOrderError: If initial_cash is negative or not a valid amount.
        """
        with self._lock:
            aid = account_id or uuid.uuid4().hex
            if aid in self._accounts:
                raise AccountAlreadyExistsError(f"Account '{aid}' already exists")

            cash = self._to_decimal(initial_cash, quant=self._cash_q)
            if cash < Decimal(0):
                raise InvalidOrderError("Initial cash cannot be negative")

            now = datetime.now(timezone.utc)
            acct = AccountPortfolio(id=aid, cash_balance=cash, created_at=now)
            self._accounts[aid] = acct
            self._holdings[aid] = {}
            self._per_account_trades[aid] = []
            return aid

    def place_order(
        self,
        account_id: str,
        side: str,
        symbol: str,
        quantity: Union[Decimal, int, float, str],
        price: Union[Decimal, int, float, str],
        memo: Optional[str] = None,
    ) -> TradeRecord:
        """
        Execute a buy or sell order for the given account and symbol.

        Args:
            account_id: The account identifier.
            side: 'buy' or 'sell' (case-insensitive).
            symbol: Asset symbol (non-empty string).
            quantity: Quantity to trade (must be > 0).
            price: Price per unit (must be > 0).
            memo: Optional note stored in the trade record.

        Returns:
            TradeRecord describing the executed trade.

        Raises:
            AccountNotFoundError: If the account does not exist.
            InvalidOrderError: If side/symbol/quantity/price are invalid.
            InsufficientCashError: If cash is insufficient for a buy order.
            InsufficientHoldingsError: If holdings are insufficient for a sell order.
        """
        with self._lock:
            account = self._get_account(account_id)

            norm_side = (side or "").strip().lower()
            if norm_side not in {"buy", "sell"}:
                raise InvalidOrderError("side must be 'buy' or 'sell'")

            sym = (symbol or "").strip()
            if not sym:
                raise InvalidOrderError("symbol must be a non-empty string")

            qty = self._to_decimal(quantity, quant=self._qty_q)
            px = self._to_decimal(price, quant=self._cash_q)

            if qty <= Decimal(0):
                raise InvalidOrderError("quantity must be greater than zero")
            if px <= Decimal(0):
                raise InvalidOrderError("price must be greater than zero")

            total = (qty * px).quantize(self._cash_q, rounding=self._rounding)

            holdings = self._holdings[account_id]
            current_pos = holdings.get(sym, Decimal(0))

            if norm_side == "buy":
                if account.cash_balance < total:
                    raise InsufficientCashError("Insufficient cash for buy order")
                # Update balances
                new_cash = (account.cash_balance - total).quantize(self._cash_q, rounding=self._rounding)
                new_pos = (current_pos + qty).quantize(self._qty_q, rounding=self._rounding)
                account.cash_balance = new_cash
                holdings[sym] = new_pos
            else:  # sell
                if qty > current_pos:
                    raise InsufficientHoldingsError("Insufficient holdings for sell order")
                new_cash = (account.cash_balance + total).quantize(self._cash_q, rounding=self._rounding)
                new_pos = (current_pos - qty).quantize(self._qty_q, rounding=self._rounding)
                account.cash_balance = new_cash
                if new_pos == Decimal(0):
                    holdings.pop(sym, None)
                else:
                    holdings[sym] = new_pos

            record = TradeRecord(
                timestamp=datetime.now(timezone.utc),
                account_id=account_id,
                side=norm_side,
                symbol=sym,
                quantity=qty,
                price=px,
                total=total,
                cash_balance_after=account.cash_balance,
                position_after=holdings.get(sym, Decimal(0)),
                memo=memo,
            )
            self._log_trade(record)
            return record

    def get_cash_balance(self, account_id: str) -> Decimal:
        """Return the current cash balance for the specified account."""
        with self._lock:
            return self._get_account(account_id).cash_balance

    def get_positions(self, account_id: str) -> Dict[str, Decimal]:
        """Return a shallow copy of the symbol->quantity positions for the account."""
        with self._lock:
            self._ensure_account_exists(account_id)
            return dict(self._holdings.get(account_id, {}))

    def get_position(self, account_id: str, symbol: str) -> Decimal:
        """Return the position size for a symbol in the given account (zero if none)."""
        with self._lock:
            self._ensure_account_exists(account_id)
            return self._holdings.get(account_id, {}).get(symbol, Decimal(0))

    def get_trades(self, account_id: Optional[str] = None) -> List[TradeRecord]:
        """
        Retrieve trade records.

        Args:
            account_id: If provided, returns trades for that account; otherwise returns all trades.

        Returns:
            A new list of TradeRecord instances in chronological order.

        Raises:
            AccountNotFoundError: If account_id is provided but does not exist.
        """
        with self._lock:
            if account_id is None:
                return list(self._trades)
            self._ensure_account_exists(account_id)
            return list(self._per_account_trades.get(account_id, []))

    def list_accounts(self) -> List[str]:
        """Return a list of all account IDs known to the engine."""
        with self._lock:
            return list(self._accounts.keys())

    # --------------------------- Internal Utils ---------------------------
    def _to_decimal(self, value: Union[Decimal, int, float, str], *, quant: Decimal) -> Decimal:
        """Convert a numeric value to a quantized Decimal using provided precision and engine's rounding."""
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
                raise InvalidOrderError(f"Unsupported numeric type: {type(value)!r}")
            return dec.quantize(quant, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidOrderError("Invalid numeric amount") from exc

    def _get_account(self, account_id: str) -> AccountPortfolio:
        acct = self._accounts.get(account_id)
        if acct is None:
            raise AccountNotFoundError(f"Account '{account_id}' not found")
        return acct

    def _ensure_account_exists(self, account_id: str) -> None:
        if account_id not in self._accounts:
            raise AccountNotFoundError(f"Account '{account_id}' not found")

    def _log_trade(self, record: TradeRecord) -> None:
        self._trades.append(record)
        self._per_account_trades.setdefault(record.account_id, []).append(record)