"""Backend account management for the trading simulation platform.

Pure-Python module (standard library only). Contains domain models,
business operations, validation, formatting, and reporting helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Callable, Iterable

import share_prices as _share_prices


class AccountError(Exception):
    """Base exception for all account-related errors."""


class ValidationError(AccountError):
    """Raised when user input is invalid."""


class InsufficientFundsError(AccountError):
    """Raised when an operation would leave cash negative."""


class InsufficientSharesError(AccountError):
    """Raised when trying to sell more shares than currently owned."""


class UnknownSymbolError(AccountError):
    """Raised when a symbol does not exist in the price lookup."""


class AccountNotCreatedError(AccountError):
    """Raised when an operation requires an account but none exists."""


class TransactionType(str, Enum):
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Transaction:
    id: int
    timestamp: datetime
    type: TransactionType
    amount: Decimal | None = None
    symbol: str | None = None
    quantity: int | None = None
    price: Decimal | None = None
    cash_balance_after: Decimal | None = None
    note: str = ""


@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: int
    current_price: Decimal
    market_value: Decimal


@dataclass(frozen=True)
class PortfolioSnapshot:
    account_name: str
    as_of: datetime
    cash_balance: Decimal
    holdings: dict[str, int]
    holding_values: list[Holding]
    total_holdings_value: Decimal
    total_portfolio_value: Decimal
    initial_deposit: Decimal
    net_cash_contributions: Decimal
    profit_loss_from_initial_deposit: Decimal
    profit_loss_from_net_contributions: Decimal


@dataclass
class Account:
    name: str
    initial_deposit: Decimal
    cash_balance: Decimal
    holdings: dict[str, int] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    next_transaction_id: int = 1


_TWO_PLACES = Decimal("0.01")


def parse_money(value: Decimal | int | float | str) -> Decimal:
    """Convert input into a two-decimal Decimal."""
    if value is None:
        raise ValidationError("Amount must not be empty.")
    if isinstance(value, bool):
        raise ValidationError("Amount must be a number.")
    try:
        if isinstance(value, Decimal):
            dec = value
        elif isinstance(value, int):
            dec = Decimal(value)
        elif isinstance(value, float):
            dec = Decimal(str(value))
        elif isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                raise ValidationError("Amount must not be empty.")
            cleaned = cleaned.replace(",", "").lstrip("$")
            dec = Decimal(cleaned)
        else:
            raise ValidationError(f"Unsupported amount type: {type(value).__name__}")
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"Invalid money value: {value!r}") from exc

    if not dec.is_finite():
        raise ValidationError("Amount must be a finite number.")
    return dec.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def parse_quantity(value: int | float | str) -> int:
    """Convert input into a positive integer share quantity."""
    if value is None:
        raise ValidationError("Quantity must not be empty.")
    if isinstance(value, bool):
        raise ValidationError("Quantity must be a positive integer.")
    if isinstance(value, int):
        qty = value
    elif isinstance(value, float):
        if not value.is_integer():
            raise ValidationError("Quantity must be a positive integer.")
        qty = int(value)
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise ValidationError("Quantity must not be empty.")
        try:
            qty = int(cleaned)
        except ValueError as exc:
            raise ValidationError(
                f"Quantity must be a positive integer (got {value!r})."
            ) from exc
    else:
        raise ValidationError(f"Unsupported quantity type: {type(value).__name__}")

    if qty <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    return qty


_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse a timestamp from supported ISO-like string formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        for fmt in _DATETIME_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        raise ValidationError(f"Invalid timestamp {value!r}. Use YYYY-MM-DD HH:MM:SS.")
    raise ValidationError(f"Unsupported timestamp type: {type(value).__name__}")


def normalize_symbol(symbol: str) -> str:
    """Strip and uppercase a share symbol."""
    if symbol is None:
        raise ValidationError("Symbol must not be empty.")
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string.")
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValidationError("Symbol must not be empty.")
    return cleaned


def format_money(value: Decimal) -> str:
    """Format a Decimal as $1,234.56."""
    if value is None:
        return ""
    quantized = Decimal(value).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    sign = "-" if quantized < 0 else ""
    abs_value = abs(quantized)
    whole, _, frac = format(abs_value, "f").partition(".")
    if not frac:
        frac = "00"
    elif len(frac) == 1:
        frac = frac + "0"
    else:
        frac = frac[:2]
    return f"{sign}${int(whole):,}.{frac}"


def _format_timestamp(ts: datetime | None) -> str:
    if ts is None:
        return ""
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def transaction_to_row(transaction: Transaction) -> list[str]:
    """Convert a Transaction to a display row."""
    return [
        str(transaction.id),
        _format_timestamp(transaction.timestamp),
        transaction.type.value,
        transaction.symbol or "",
        "" if transaction.quantity is None else str(transaction.quantity),
        "" if transaction.price is None else format_money(transaction.price),
        "" if transaction.amount is None else format_money(transaction.amount),
        "" if transaction.cash_balance_after is None else format_money(transaction.cash_balance_after),
        transaction.note or "",
    ]


def holding_to_row(holding: Holding) -> list[str]:
    """Convert a Holding to a display row."""
    return [
        holding.symbol,
        str(holding.quantity),
        format_money(holding.current_price),
        format_money(holding.market_value),
    ]


def snapshot_to_summary_lines(snapshot: PortfolioSnapshot) -> list[str]:
    """Render a portfolio snapshot as display lines."""
    return [
        f"**Account:** {snapshot.account_name}",
        f"**As of:** {_format_timestamp(snapshot.as_of)}",
        f"**Cash Balance:** {format_money(snapshot.cash_balance)}",
        f"**Holdings Value:** {format_money(snapshot.total_holdings_value)}",
        f"**Total Portfolio Value:** {format_money(snapshot.total_portfolio_value)}",
        f"**Initial Deposit:** {format_money(snapshot.initial_deposit)}",
        f"**Net Cash Contributions:** {format_money(snapshot.net_cash_contributions)}",
        f"**P/L vs Initial Deposit:** {format_money(snapshot.profit_loss_from_initial_deposit)}",
        f"**P/L vs Net Contributions:** {format_money(snapshot.profit_loss_from_net_contributions)}",
    ]


class AccountService:
    """Main API used by the Gradio frontend and tests."""

    def __init__(self, price_provider: Callable[[str], Decimal]) -> None:
        self._price_provider = price_provider

    def _now(self, timestamp: datetime | None) -> datetime:
        return timestamp if timestamp is not None else datetime.now()

    def _get_price(self, symbol: str) -> Decimal:
        try:
            price = self._price_provider(symbol)
        except _share_prices.UnknownSymbolError as exc:
            raise UnknownSymbolError(str(exc)) from exc
        except _share_prices.ValidationError as exc:
            raise ValidationError(str(exc)) from exc
        except ValueError as exc:
            raise UnknownSymbolError(str(exc)) from exc
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        return price.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def _next_transaction(self, account: Account) -> int:
        tid = account.next_transaction_id
        account.next_transaction_id += 1
        return tid

    def create_account(
        self,
        name: str,
        initial_deposit: Decimal | int | float | str,
        timestamp: datetime | None = None,
    ) -> Account:
        if name is None or not isinstance(name, str) or not name.strip():
            raise ValidationError("Account name must not be empty.")
        deposit = parse_money(initial_deposit)
        if deposit < Decimal("0.00"):
            raise ValidationError("Initial deposit must not be negative.")
        ts = self._now(timestamp)
        account = Account(
            name=name.strip(),
            initial_deposit=deposit,
            cash_balance=deposit,
            holdings={},
            transactions=[],
            created_at=ts,
            next_transaction_id=1,
        )
        account.transactions.append(
            Transaction(
                id=self._next_transaction(account),
                timestamp=ts,
                type=TransactionType.CREATE_ACCOUNT,
                amount=deposit if deposit > 0 else None,
                cash_balance_after=deposit,
                note=f"Account '{name.strip()}' created.",
            )
        )
        return account

    def deposit(
        self,
        account: Account,
        amount: Decimal | int | float | str,
        timestamp: datetime | None = None,
    ) -> Account:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        amt = parse_money(amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Deposit amount must be greater than zero.")
        ts = self._now(timestamp)
        account.cash_balance += amt
        account.transactions.append(
            Transaction(
                id=self._next_transaction(account),
                timestamp=ts,
                type=TransactionType.DEPOSIT,
                amount=amt,
                cash_balance_after=account.cash_balance,
                note="Cash deposit.",
            )
        )
        return account

    def withdraw(
        self,
        account: Account,
        amount: Decimal | int | float | str,
        timestamp: datetime | None = None,
    ) -> Account:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        amt = parse_money(amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Withdrawal amount must be greater than zero.")
        if amt > account.cash_balance:
            raise InsufficientFundsError(
                f"Cannot withdraw {format_money(amt)}: cash balance is {format_money(account.cash_balance)}."
            )
        ts = self._now(timestamp)
        account.cash_balance -= amt
        account.transactions.append(
            Transaction(
                id=self._next_transaction(account),
                timestamp=ts,
                type=TransactionType.WITHDRAW,
                amount=amt,
                cash_balance_after=account.cash_balance,
                note="Cash withdrawal.",
            )
        )
        return account

    def buy(
        self,
        account: Account,
        symbol: str,
        quantity: int | float | str,
        timestamp: datetime | None = None,
    ) -> Account:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        sym = normalize_symbol(symbol)
        qty = parse_quantity(quantity)
        price = self._get_price(sym)
        total_cost = (price * qty).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        if total_cost > account.cash_balance:
            raise InsufficientFundsError(
                f"Cannot buy {qty} {sym} for {format_money(total_cost)}: cash balance is {format_money(account.cash_balance)}."
            )
        ts = self._now(timestamp)
        account.cash_balance -= total_cost
        account.holdings[sym] = account.holdings.get(sym, 0) + qty
        account.transactions.append(
            Transaction(
                id=self._next_transaction(account),
                timestamp=ts,
                type=TransactionType.BUY,
                amount=total_cost,
                symbol=sym,
                quantity=qty,
                price=price,
                cash_balance_after=account.cash_balance,
                note=f"Bought {qty} {sym} @ {format_money(price)}.",
            )
        )
        return account

    def sell(
        self,
        account: Account,
        symbol: str,
        quantity: int | float | str,
        timestamp: datetime | None = None,
    ) -> Account:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        sym = normalize_symbol(symbol)
        qty = parse_quantity(quantity)
        held = account.holdings.get(sym, 0)
        if qty > held:
            raise InsufficientSharesError(f"Cannot sell {qty} {sym}: only {held} held.")
        price = self._get_price(sym)
        proceeds = (price * qty).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        ts = self._now(timestamp)
        new_held = held - qty
        if new_held == 0:
            account.holdings.pop(sym, None)
        else:
            account.holdings[sym] = new_held
        account.cash_balance += proceeds
        account.transactions.append(
            Transaction(
                id=self._next_transaction(account),
                timestamp=ts,
                type=TransactionType.SELL,
                amount=proceeds,
                symbol=sym,
                quantity=qty,
                price=price,
                cash_balance_after=account.cash_balance,
                note=f"Sold {qty} {sym} @ {format_money(price)}.",
            )
        )
        return account

    def get_holdings(self, account: Account) -> dict[str, int]:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        return {symbol: qty for symbol, qty in account.holdings.items() if qty > 0}

    def _transactions_up_to(self, account: Account, as_of: datetime) -> list[Transaction]:
        return [tx for tx in account.transactions if tx.timestamp <= as_of]

    def get_holdings_at(self, account: Account, as_of: datetime | None) -> dict[str, int]:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        if as_of is None:
            return self.get_holdings(account)
        holdings: dict[str, int] = {}
        for tx in self._transactions_up_to(account, as_of):
            if tx.type is TransactionType.BUY and tx.symbol and tx.quantity:
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) + tx.quantity
            elif tx.type is TransactionType.SELL and tx.symbol and tx.quantity:
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) - tx.quantity
                if holdings[tx.symbol] <= 0:
                    holdings.pop(tx.symbol, None)
        return holdings

    def get_cash_balance_at(self, account: Account, as_of: datetime | None) -> Decimal:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        if as_of is None:
            return account.cash_balance
        balance = Decimal("0.00")
        for tx in self._transactions_up_to(account, as_of):
            if tx.type in (TransactionType.CREATE_ACCOUNT, TransactionType.DEPOSIT, TransactionType.SELL):
                balance += tx.amount or Decimal("0.00")
            elif tx.type in (TransactionType.WITHDRAW, TransactionType.BUY):
                balance -= tx.amount or Decimal("0.00")
        return balance.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def _net_contributions_at(self, account: Account, as_of: datetime | None) -> Decimal:
        transactions: Iterable[Transaction] = account.transactions if as_of is None else self._transactions_up_to(account, as_of)
        total = Decimal("0.00")
        for tx in transactions:
            if tx.type in (TransactionType.CREATE_ACCOUNT, TransactionType.DEPOSIT):
                total += tx.amount or Decimal("0.00")
            elif tx.type is TransactionType.WITHDRAW:
                total -= tx.amount or Decimal("0.00")
        return total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def get_portfolio_snapshot(self, account: Account, as_of: datetime | None = None) -> PortfolioSnapshot:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        snapshot_time = as_of if as_of is not None else datetime.now()
        cash = account.cash_balance if as_of is None else self.get_cash_balance_at(account, as_of)
        holdings = self.get_holdings(account) if as_of is None else self.get_holdings_at(account, as_of)
        holding_values: list[Holding] = []
        total_holdings_value = Decimal("0.00")
        for sym in sorted(holdings):
            qty = holdings[sym]
            try:
                price = self._get_price(sym)
            except UnknownSymbolError:
                price = Decimal("0.00")
            market_value = (price * qty).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
            holding_values.append(Holding(sym, qty, price, market_value))
            total_holdings_value += market_value
        total_holdings_value = total_holdings_value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        total_portfolio_value = (cash + total_holdings_value).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        net_contributions = self._net_contributions_at(account, as_of)
        pl_initial = (total_portfolio_value - account.initial_deposit).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        pl_net = (total_portfolio_value - net_contributions).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        return PortfolioSnapshot(
            account_name=account.name,
            as_of=snapshot_time,
            cash_balance=cash.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP),
            holdings=dict(holdings),
            holding_values=holding_values,
            total_holdings_value=total_holdings_value,
            total_portfolio_value=total_portfolio_value,
            initial_deposit=account.initial_deposit,
            net_cash_contributions=net_contributions,
            profit_loss_from_initial_deposit=pl_initial,
            profit_loss_from_net_contributions=pl_net,
        )

    def get_profit_loss(self, account: Account, as_of: datetime | None = None) -> Decimal:
        return self.get_portfolio_snapshot(account, as_of).profit_loss_from_initial_deposit

    def list_transactions(self, account: Account, as_of: datetime | None = None) -> list[Transaction]:
        if account is None:
            raise AccountNotCreatedError("No account exists. Create one first.")
        if as_of is None:
            return list(account.transactions)
        return self._transactions_up_to(account, as_of)


__all__ = [
    "AccountError",
    "ValidationError",
    "InsufficientFundsError",
    "InsufficientSharesError",
    "UnknownSymbolError",
    "AccountNotCreatedError",
    "TransactionType",
    "Transaction",
    "Holding",
    "PortfolioSnapshot",
    "Account",
    "AccountService",
    "parse_money",
    "parse_quantity",
    "parse_datetime",
    "normalize_symbol",
    "format_money",
    "transaction_to_row",
    "holding_to_row",
    "snapshot_to_summary_lines",
]
