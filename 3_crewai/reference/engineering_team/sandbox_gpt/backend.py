"""Backend for a simple trading simulation account management system.

The module is intentionally framework-independent and uses in-memory storage only.
Money and share quantities are represented with :class:`decimal.Decimal`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Callable, Optional
from uuid import uuid4


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AccountError(Exception):
    """Base exception for expected account-management errors."""


class AccountNotFoundError(AccountError):
    """Raised when an operation references an unknown account."""


class DuplicateAccountError(AccountError):
    """Raised when trying to create an account with an existing ID."""


class InvalidAmountError(AccountError):
    """Raised when a deposit, withdrawal, price, or amount is invalid."""


class InvalidQuantityError(AccountError):
    """Raised when a buy or sell quantity is invalid."""


class InsufficientFundsError(AccountError):
    """Raised when a withdrawal or buy would exceed available cash."""


class InsufficientHoldingsError(AccountError):
    """Raised when a sell would exceed owned shares."""


class UnknownSymbolError(AccountError):
    """Raised when an unsupported share symbol is requested."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    account_id: str
    timestamp: datetime
    type: str
    symbol: Optional[str]
    quantity: Decimal
    price: Decimal
    cash_amount: Decimal
    cash_balance_after: Decimal


@dataclass
class Account:
    account_id: str
    name: str
    cash_balance: Decimal
    initial_deposit: Decimal
    created_at: datetime
    transactions: list[Transaction] = field(default_factory=list)


@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    as_of: datetime
    cash_balance: Decimal
    holdings: dict[str, Decimal]
    holdings_value: Decimal
    total_value: Decimal
    net_contributions: Decimal
    profit_loss: Decimal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SUPPORTED_PRICES: dict[str, Decimal] = {
    "AAPL": Decimal("150.00"),
    "TSLA": Decimal("250.00"),
    "GOOGL": Decimal("2800.00"),
}

ZERO = Decimal("0")
CENT = Decimal("0.01")


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def generate_transaction_id() -> str:
    """Generate a unique transaction ID using standard-library UUIDs."""

    return str(uuid4())


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Convert supported numeric input to ``Decimal``.

    Floats are converted via ``str(value)`` to avoid binary floating-point
    artifacts. Strings are stripped before conversion.

    Raises:
        InvalidAmountError: if the value cannot be converted to a finite
            ``Decimal``.
    """

    if isinstance(value, bool):
        raise InvalidAmountError("Boolean values are not valid numeric amounts")

    try:
        if isinstance(value, Decimal):
            result = value
        elif isinstance(value, int):
            result = Decimal(value)
        elif isinstance(value, float):
            result = Decimal(str(value))
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise InvalidAmountError("Amount cannot be empty")
            result = Decimal(stripped)
        else:
            raise InvalidAmountError(f"Unsupported numeric value: {value!r}")
    except (InvalidOperation, ValueError) as exc:
        raise InvalidAmountError(f"Invalid numeric value: {value!r}") from exc

    if not result.is_finite():
        raise InvalidAmountError(f"Invalid numeric value: {value!r}")
    return result


def _require_positive_amount(value: Decimal | int | float | str, label: str = "Amount") -> Decimal:
    amount = to_decimal(value)
    if amount <= ZERO:
        raise InvalidAmountError(f"{label} must be greater than zero")
    return amount


def _require_positive_quantity(value: Decimal | int | float | str) -> Decimal:
    try:
        quantity = to_decimal(value)
    except InvalidAmountError as exc:
        raise InvalidQuantityError(str(exc)) from exc
    if quantity <= ZERO:
        raise InvalidQuantityError("Quantity must be greater than zero")
    return quantity


def normalize_symbol(symbol: str) -> str:
    """Strip whitespace and convert a symbol to uppercase.

    Raises:
        UnknownSymbolError: if the symbol is empty or not a string.
    """

    if not isinstance(symbol, str):
        raise UnknownSymbolError("Symbol must be a string")
    normalized = symbol.strip().upper()
    if not normalized:
        raise UnknownSymbolError("Symbol cannot be empty")
    return normalized


def _normalize_account_id(account_id: str) -> str:
    if not isinstance(account_id, str):
        raise AccountError("Account ID must be a string")
    normalized = account_id.strip()
    if not normalized:
        raise AccountError("Account ID cannot be empty")
    return normalized


def _normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise AccountError("Name must be a string")
    normalized = name.strip()
    if not normalized:
        raise AccountError("Name cannot be empty")
    return normalized


def get_share_price(symbol: str) -> Decimal:
    """Return the current fixed test price for a supported share symbol.

    Supported symbols are AAPL, TSLA, and GOOGL. Symbols are normalized to
    uppercase. Unsupported symbols raise ``UnknownSymbolError``.
    """

    normalized = normalize_symbol(symbol)
    try:
        return SUPPORTED_PRICES[normalized]
    except KeyError as exc:
        raise UnknownSymbolError(f"Unsupported symbol: {normalized}") from exc


def format_money(value: Decimal) -> str:
    """Format a Decimal as money, e.g. ``Decimal('123.4') -> '$123.40'``."""

    amount = to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
    prefix = "-$" if amount < ZERO else "$"
    return f"{prefix}{abs(amount):,.2f}"


def format_decimal(value: Decimal) -> str:
    """Format a Decimal quantity without unnecessary trailing zeroes."""

    number = to_decimal(value)
    if number == ZERO:
        return "0"
    text = format(number.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def transaction_to_row(transaction: Transaction) -> list[str]:
    """Serialize a transaction for table display."""

    return [
        transaction.timestamp.isoformat(),
        transaction.type,
        transaction.symbol or "",
        format_decimal(transaction.quantity),
        format_money(transaction.price),
        format_money(transaction.cash_amount),
        format_money(transaction.cash_balance_after),
        transaction.transaction_id,
    ]


def holdings_to_rows(
    holdings: dict[str, Decimal],
    price_provider: Callable[[str], Decimal] = get_share_price,
) -> list[list[str]]:
    """Serialize holdings for table display.

    Output columns: Symbol, Quantity, Current Price, Market Value.
    """

    rows: list[list[str]] = []
    for symbol in sorted(holdings):
        quantity = holdings[symbol]
        price = price_provider(symbol)
        market_value = price * quantity
        rows.append(
            [
                symbol,
                format_decimal(quantity),
                format_money(price),
                format_money(market_value),
            ]
        )
    return rows


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AccountService:
    """In-memory account-management API for the trading simulation."""

    def __init__(
        self,
        price_provider: Callable[[str], Decimal] = get_share_price,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._accounts: dict[str, Account] = {}
        self._price_provider = price_provider
        self._clock = clock or utc_now

    def create_account(
        self,
        account_id: str,
        name: str,
        initial_deposit: Decimal | int | float | str,
    ) -> Account:
        normalized_id = _normalize_account_id(account_id)
        normalized_name = _normalize_name(name)
        deposit_amount = _require_positive_amount(initial_deposit, "Initial deposit")

        if normalized_id in self._accounts:
            raise DuplicateAccountError(f"Account already exists: {normalized_id}")

        timestamp = self._clock()
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=normalized_id,
            timestamp=timestamp,
            type="DEPOSIT",
            symbol=None,
            quantity=ZERO,
            price=ZERO,
            cash_amount=deposit_amount,
            cash_balance_after=deposit_amount,
        )
        account = Account(
            account_id=normalized_id,
            name=normalized_name,
            cash_balance=deposit_amount,
            initial_deposit=deposit_amount,
            created_at=timestamp,
            transactions=[transaction],
        )
        self._accounts[normalized_id] = account
        return account

    def get_account(self, account_id: str) -> Account:
        normalized_id = _normalize_account_id(account_id)
        try:
            return self._accounts[normalized_id]
        except KeyError as exc:
            raise AccountNotFoundError(f"Account not found: {normalized_id}") from exc

    def list_accounts(self) -> list[Account]:
        return sorted(self._accounts.values(), key=lambda account: account.created_at)

    def deposit(self, account_id: str, amount: Decimal | int | float | str) -> Transaction:
        account = self.get_account(account_id)
        deposit_amount = _require_positive_amount(amount)

        new_balance = account.cash_balance + deposit_amount
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=account.account_id,
            timestamp=self._clock(),
            type="DEPOSIT",
            symbol=None,
            quantity=ZERO,
            price=ZERO,
            cash_amount=deposit_amount,
            cash_balance_after=new_balance,
        )
        account.cash_balance = new_balance
        account.transactions.append(transaction)
        return transaction

    def withdraw(self, account_id: str, amount: Decimal | int | float | str) -> Transaction:
        account = self.get_account(account_id)
        withdrawal_amount = _require_positive_amount(amount)

        if withdrawal_amount > account.cash_balance:
            raise InsufficientFundsError("Withdrawal exceeds available cash balance")

        new_balance = account.cash_balance - withdrawal_amount
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=account.account_id,
            timestamp=self._clock(),
            type="WITHDRAW",
            symbol=None,
            quantity=ZERO,
            price=ZERO,
            cash_amount=-withdrawal_amount,
            cash_balance_after=new_balance,
        )
        account.cash_balance = new_balance
        account.transactions.append(transaction)
        return transaction

    def buy(
        self,
        account_id: str,
        symbol: str,
        quantity: Decimal | int | float | str,
    ) -> Transaction:
        account = self.get_account(account_id)
        normalized_symbol = normalize_symbol(symbol)
        buy_quantity = _require_positive_quantity(quantity)
        price = self._price_provider(normalized_symbol)
        price = _require_positive_amount(price, "Share price")
        total_cost = price * buy_quantity

        if total_cost > account.cash_balance:
            raise InsufficientFundsError("Buy cost exceeds available cash balance")

        new_balance = account.cash_balance - total_cost
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=account.account_id,
            timestamp=self._clock(),
            type="BUY",
            symbol=normalized_symbol,
            quantity=buy_quantity,
            price=price,
            cash_amount=-total_cost,
            cash_balance_after=new_balance,
        )
        account.cash_balance = new_balance
        account.transactions.append(transaction)
        return transaction

    def sell(
        self,
        account_id: str,
        symbol: str,
        quantity: Decimal | int | float | str,
    ) -> Transaction:
        account = self.get_account(account_id)
        normalized_symbol = normalize_symbol(symbol)
        sell_quantity = _require_positive_quantity(quantity)
        current_quantity = self.get_holdings(account.account_id).get(normalized_symbol, ZERO)

        if sell_quantity > current_quantity:
            raise InsufficientHoldingsError("Sell quantity exceeds current holdings")

        price = self._price_provider(normalized_symbol)
        price = _require_positive_amount(price, "Share price")
        proceeds = price * sell_quantity
        new_balance = account.cash_balance + proceeds
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=account.account_id,
            timestamp=self._clock(),
            type="SELL",
            symbol=normalized_symbol,
            quantity=sell_quantity,
            price=price,
            cash_amount=proceeds,
            cash_balance_after=new_balance,
        )
        account.cash_balance = new_balance
        account.transactions.append(transaction)
        return transaction

    def get_holdings(self, account_id: str) -> dict[str, Decimal]:
        account = self.get_account(account_id)
        return self._replay_holdings(account.transactions)

    def get_holdings_at(self, account_id: str, as_of: datetime) -> dict[str, Decimal]:
        account = self.get_account(account_id)
        return self._replay_holdings(self._transactions_at_or_before(account, as_of))

    def get_cash_balance_at(self, account_id: str, as_of: datetime) -> Decimal:
        account = self.get_account(account_id)
        return sum(
            (transaction.cash_amount for transaction in self._transactions_at_or_before(account, as_of)),
            ZERO,
        )

    def get_net_contributions(self, account_id: str, as_of: datetime | None = None) -> Decimal:
        account = self.get_account(account_id)
        transactions = account.transactions if as_of is None else self._transactions_at_or_before(account, as_of)
        total = ZERO
        for transaction in transactions:
            if transaction.type in {"DEPOSIT", "WITHDRAW"}:
                total += transaction.cash_amount
        return total

    def get_portfolio_value(self, account_id: str) -> Decimal:
        account = self.get_account(account_id)
        holdings = self.get_holdings(account.account_id)
        return account.cash_balance + self._holdings_value(holdings)

    def get_portfolio_value_at(self, account_id: str, as_of: datetime) -> Decimal:
        cash_balance = self.get_cash_balance_at(account_id, as_of)
        holdings = self.get_holdings_at(account_id, as_of)
        return cash_balance + self._holdings_value(holdings)

    def get_profit_loss(self, account_id: str) -> Decimal:
        return self.get_portfolio_value(account_id) - self.get_net_contributions(account_id)

    def get_profit_loss_at(self, account_id: str, as_of: datetime) -> Decimal:
        return self.get_portfolio_value_at(account_id, as_of) - self.get_net_contributions(account_id, as_of)

    def get_snapshot(self, account_id: str) -> AccountSnapshot:
        account = self.get_account(account_id)
        as_of = self._clock()
        holdings = self.get_holdings(account.account_id)
        holdings_value = self._holdings_value(holdings)
        total_value = account.cash_balance + holdings_value
        net_contributions = self.get_net_contributions(account.account_id)
        return AccountSnapshot(
            account_id=account.account_id,
            as_of=as_of,
            cash_balance=account.cash_balance,
            holdings=holdings,
            holdings_value=holdings_value,
            total_value=total_value,
            net_contributions=net_contributions,
            profit_loss=total_value - net_contributions,
        )

    def get_snapshot_at(self, account_id: str, as_of: datetime) -> AccountSnapshot:
        account = self.get_account(account_id)
        holdings = self.get_holdings_at(account.account_id, as_of)
        cash_balance = self.get_cash_balance_at(account.account_id, as_of)
        holdings_value = self._holdings_value(holdings)
        total_value = cash_balance + holdings_value
        net_contributions = self.get_net_contributions(account.account_id, as_of)
        return AccountSnapshot(
            account_id=account.account_id,
            as_of=as_of,
            cash_balance=cash_balance,
            holdings=holdings,
            holdings_value=holdings_value,
            total_value=total_value,
            net_contributions=net_contributions,
            profit_loss=total_value - net_contributions,
        )

    def list_transactions(
        self,
        account_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Transaction]:
        account = self.get_account(account_id)
        transactions = account.transactions
        if start is not None:
            transactions = [transaction for transaction in transactions if transaction.timestamp >= start]
        if end is not None:
            transactions = [transaction for transaction in transactions if transaction.timestamp <= end]
        return sorted(transactions, key=lambda transaction: transaction.timestamp)

    @staticmethod
    def _transactions_at_or_before(account: Account, as_of: datetime) -> list[Transaction]:
        return [transaction for transaction in account.transactions if transaction.timestamp <= as_of]

    @staticmethod
    def _replay_holdings(transactions: list[Transaction]) -> dict[str, Decimal]:
        holdings: dict[str, Decimal] = {}
        for transaction in transactions:
            if transaction.type == "BUY" and transaction.symbol is not None:
                holdings[transaction.symbol] = holdings.get(transaction.symbol, ZERO) + transaction.quantity
            elif transaction.type == "SELL" and transaction.symbol is not None:
                holdings[transaction.symbol] = holdings.get(transaction.symbol, ZERO) - transaction.quantity
        return {symbol: quantity for symbol, quantity in sorted(holdings.items()) if quantity != ZERO}

    def _holdings_value(self, holdings: dict[str, Decimal]) -> Decimal:
        total = ZERO
        for symbol, quantity in holdings.items():
            price = self._price_provider(symbol)
            price = _require_positive_amount(price, "Share price")
            total += price * quantity
        return total


__all__ = [
    "get_share_price",
    "AccountService",
    "Transaction",
    "Account",
    "AccountSnapshot",
    "AccountError",
    "AccountNotFoundError",
    "DuplicateAccountError",
    "InvalidAmountError",
    "InvalidQuantityError",
    "InsufficientFundsError",
    "InsufficientHoldingsError",
    "UnknownSymbolError",
    "to_decimal",
    "normalize_symbol",
    "format_money",
    "format_decimal",
    "transaction_to_row",
    "holdings_to_rows",
    "generate_transaction_id",
    "utc_now",
]
