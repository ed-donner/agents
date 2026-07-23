from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

SUPPORTED_SYMBOLS: tuple[str, ...] = ("AAPL", "TSLA", "GOOGL")

_FIXED_PRICES = {
    "AAPL": 180.0,
    "TSLA": 250.0,
    "GOOGL": 140.0,
}


class AccountError(Exception):
    pass


class UnknownSymbolError(AccountError):
    pass


class ValidationError(AccountError):
    pass


class InsufficientFundsError(AccountError):
    pass


class InsufficientHoldingsError(AccountError):
    pass


class AccountNotInitializedError(AccountError):
    pass


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    timestamp: datetime
    transaction_type: TransactionType
    symbol: Optional[str]
    quantity: int
    price: Optional[float]
    cash_amount: float
    cash_balance_after: float
    notes: str = ""


@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    user_name: str
    timestamp: datetime
    cash_balance: float
    holdings: dict[str, int]
    holdings_value: float
    total_portfolio_value: float
    net_cash_contributed: float
    profit_loss: float


@dataclass
class Account:
    account_id: str
    user_name: str
    cash_balance: float = 0.0
    holdings: dict[str, int] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)
    initial_deposit: Optional[float] = None
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0


def get_share_price(symbol: str) -> float:
    normalized = symbol.strip().upper()
    if normalized not in _FIXED_PRICES:
        raise UnknownSymbolError(f"Unsupported symbol: {symbol}")
    return _FIXED_PRICES[normalized]


class AccountService:
    def __init__(self, account: Account, price_lookup: Callable[[str], float] = get_share_price) -> None:
        self.account = account
        self.price_lookup = price_lookup

    @classmethod
    def create_account(
        cls,
        user_name: str,
        account_id: Optional[str] = None,
        price_lookup: Callable[[str], float] = get_share_price,
    ) -> "AccountService":
        if not user_name or not user_name.strip():
            raise ValidationError("user_name must be non-empty")
        if account_id is None:
            account_id = f"ACC-{uuid4().hex[:12].upper()}"
        return cls(Account(account_id=account_id, user_name=user_name.strip()), price_lookup=price_lookup)

    def deposit(self, amount: float, timestamp: Optional[datetime] = None) -> Transaction:
        self._validate_positive_amount(amount)
        self.account.cash_balance += amount
        self.account.total_deposits += amount
        if self.account.initial_deposit is None:
            self.account.initial_deposit = amount
        return self._record_transaction(TransactionType.DEPOSIT, None, 0, None, amount, timestamp)

    def withdraw(self, amount: float, timestamp: Optional[datetime] = None) -> Transaction:
        self._validate_positive_amount(amount)
        if amount > self.account.cash_balance:
            raise InsufficientFundsError("Insufficient cash balance")
        self.account.cash_balance -= amount
        self.account.total_withdrawals += amount
        return self._record_transaction(TransactionType.WITHDRAWAL, None, 0, None, -amount, timestamp)

    def buy(self, symbol: str, quantity: int, timestamp: Optional[datetime] = None) -> Transaction:
        normalized = self._normalize_symbol(symbol)
        self._validate_positive_quantity(quantity)
        price = self.price_lookup(normalized)
        total_cost = price * quantity
        if total_cost > self.account.cash_balance:
            raise InsufficientFundsError("Insufficient cash to buy shares")
        self.account.cash_balance -= total_cost
        self.account.holdings[normalized] = self.account.holdings.get(normalized, 0) + quantity
        return self._record_transaction(TransactionType.BUY, normalized, quantity, price, -total_cost, timestamp)

    def sell(self, symbol: str, quantity: int, timestamp: Optional[datetime] = None) -> Transaction:
        normalized = self._normalize_symbol(symbol)
        self._validate_positive_quantity(quantity)
        owned = self.account.holdings.get(normalized, 0)
        if quantity > owned:
            raise InsufficientHoldingsError("Insufficient holdings to sell shares")
        price = self.price_lookup(normalized)
        proceeds = price * quantity
        new_qty = owned - quantity
        if new_qty:
            self.account.holdings[normalized] = new_qty
        else:
            self.account.holdings.pop(normalized, None)
        self.account.cash_balance += proceeds
        return self._record_transaction(TransactionType.SELL, normalized, quantity, price, proceeds, timestamp)

    def get_cash_balance(self) -> float:
        return self.account.cash_balance

    def get_holdings(self) -> dict[str, int]:
        return dict(self.account.holdings)

    def get_holdings_value(self) -> float:
        return sum(qty * self.price_lookup(sym) for sym, qty in self.account.holdings.items())

    def get_total_portfolio_value(self) -> float:
        return self.get_cash_balance() + self.get_holdings_value()

    def get_net_cash_contributed(self) -> float:
        return self.account.total_deposits - self.account.total_withdrawals

    def get_profit_loss(self) -> float:
        return self.get_total_portfolio_value() - self.get_net_cash_contributed()

    def get_transactions(self) -> list[Transaction]:
        return list(self.account.transactions)

    def get_snapshot(self, timestamp: Optional[datetime] = None) -> AccountSnapshot:
        if timestamp is None:
            return self._build_snapshot_from_state(
                self.account.cash_balance,
                dict(self.account.holdings),
                self.account.total_deposits,
                self.account.total_withdrawals,
                datetime.now(),
            )
        cash_balance, holdings, total_deposits, total_withdrawals = self._replay_until(timestamp)
        return self._build_snapshot_from_state(cash_balance, holdings, total_deposits, total_withdrawals, timestamp)

    def get_holdings_at(self, timestamp: datetime) -> dict[str, int]:
        return self.get_snapshot(timestamp).holdings

    def get_profit_loss_at(self, timestamp: datetime) -> float:
        return self.get_snapshot(timestamp).profit_loss

    def get_transactions_until(self, timestamp: datetime) -> list[Transaction]:
        return [t for t in self.account.transactions if t.timestamp <= timestamp]

    def _record_transaction(
        self,
        transaction_type: TransactionType,
        symbol: Optional[str],
        quantity: int,
        price: Optional[float],
        cash_amount: float,
        timestamp: Optional[datetime],
        notes: str = "",
    ) -> Transaction:
        tx = Transaction(
            transaction_id=len(self.account.transactions) + 1,
            timestamp=timestamp or datetime.now(),
            transaction_type=transaction_type,
            symbol=symbol,
            quantity=quantity,
            price=price,
            cash_amount=cash_amount,
            cash_balance_after=self.account.cash_balance,
            notes=notes,
        )
        self.account.transactions.append(tx)
        return tx

    def _normalize_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        try:
            self.price_lookup(normalized)
        except AccountError:
            raise
        except Exception as exc:
            raise UnknownSymbolError(str(exc)) from exc
        if normalized not in SUPPORTED_SYMBOLS:
            raise UnknownSymbolError(f"Unsupported symbol: {symbol}")
        return normalized

    def _validate_positive_amount(self, amount: float, field_name: str = "amount") -> None:
        if amount is None or amount <= 0:
            raise ValidationError(f"{field_name} must be greater than zero")

    def _validate_positive_quantity(self, quantity: int) -> None:
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("quantity must be a positive integer")

    def _build_snapshot_from_state(
        self,
        cash_balance: float,
        holdings: dict[str, int],
        total_deposits: float,
        total_withdrawals: float,
        timestamp: datetime,
    ) -> AccountSnapshot:
        holdings_value = sum(qty * self.price_lookup(sym) for sym, qty in holdings.items())
        total_portfolio_value = cash_balance + holdings_value
        net_cash_contributed = total_deposits - total_withdrawals
        profit_loss = total_portfolio_value - net_cash_contributed
        return AccountSnapshot(
            account_id=self.account.account_id,
            user_name=self.account.user_name,
            timestamp=timestamp,
            cash_balance=cash_balance,
            holdings=holdings,
            holdings_value=holdings_value,
            total_portfolio_value=total_portfolio_value,
            net_cash_contributed=net_cash_contributed,
            profit_loss=profit_loss,
        )

    def _replay_until(self, timestamp: datetime) -> tuple[float, dict[str, int], float, float]:
        cash_balance = 0.0
        holdings: dict[str, int] = {}
        total_deposits = 0.0
        total_withdrawals = 0.0
        for tx in self.account.transactions:
            if tx.timestamp > timestamp:
                continue
            if tx.transaction_type == TransactionType.DEPOSIT:
                cash_balance += tx.cash_amount
                total_deposits += tx.cash_amount
            elif tx.transaction_type == TransactionType.WITHDRAWAL:
                cash_balance += tx.cash_amount
                total_withdrawals += -tx.cash_amount
            elif tx.transaction_type == TransactionType.BUY:
                cash_balance += tx.cash_amount
                holdings[tx.symbol or ""] = holdings.get(tx.symbol or "", 0) + tx.quantity
            elif tx.transaction_type == TransactionType.SELL:
                cash_balance += tx.cash_amount
                if tx.symbol:
                    holdings[tx.symbol] = holdings.get(tx.symbol, 0) - tx.quantity
                    if holdings[tx.symbol] <= 0:
                        holdings.pop(tx.symbol, None)
        return cash_balance, holdings, total_deposits, total_withdrawals


def transaction_to_row(transaction: Transaction) -> list[Any]:
    return [
        transaction.transaction_id,
        transaction.timestamp.isoformat(sep=" ", timespec="seconds"),
        transaction.transaction_type.value,
        transaction.symbol,
        transaction.quantity,
        transaction.price,
        transaction.cash_amount,
        transaction.cash_balance_after,
        transaction.notes,
    ]


def transactions_to_rows(transactions: list[Transaction]) -> list[list[Any]]:
    return [transaction_to_row(tx) for tx in transactions]


def holdings_to_rows(
    holdings: dict[str, int],
    price_lookup: Callable[[str], float] = get_share_price,
) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for symbol, quantity in holdings.items():
        price = price_lookup(symbol)
        rows.append([symbol, quantity, price, quantity * price])
    return rows


def snapshot_to_summary(snapshot: AccountSnapshot) -> str:
    return (
        f"Account: {snapshot.account_id}\n"
        f"User: {snapshot.user_name}\n"
        f"Timestamp: {snapshot.timestamp.isoformat(sep=' ', timespec='seconds')}\n"
        f"Cash Balance: ${snapshot.cash_balance:,.2f}\n"
        f"Holdings Value: ${snapshot.holdings_value:,.2f}\n"
        f"Total Portfolio Value: ${snapshot.total_portfolio_value:,.2f}\n"
        f"Net Cash Contributed: ${snapshot.net_cash_contributed:,.2f}\n"
        f"Profit/Loss: ${snapshot.profit_loss:,.2f}"
    )
