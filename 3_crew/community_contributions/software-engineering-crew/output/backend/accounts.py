from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, List, Optional, Union
import threading
import uuid


class AccountError(Exception):
    """Base class for account-related errors."""


class AccountNotFoundError(AccountError):
    """Raised when an account does not exist."""


class AccountAlreadyExistsError(AccountError):
    """Raised when an account already exists."""


class InsufficientFundsError(AccountError):
    """Raised when a withdrawal exceeds the available balance."""


class InvalidAmountError(AccountError):
    """Raised when an amount is invalid (non-numeric, negative, or zero where not allowed)."""


@dataclass
class Account:
    """Represents an account with a balance and creation timestamp."""

    id: str
    balance: Decimal
    created_at: datetime


@dataclass(frozen=True)
class LedgerEntry:
    """Represents an immutable ledger entry for an account operation."""

    timestamp: datetime
    account_id: str
    type: str  # 'create', 'deposit', 'withdrawal'
    amount: Decimal
    balance_after: Decimal
    memo: Optional[str] = None


class AccountService:
    """
    Service for managing accounts, balances, deposits, and withdrawals with
    validation and immutable ledger logging.

    - Uses Decimal for monetary values with configurable precision (default 2).
    - Provides methods to create accounts, deposit, withdraw, and query balances.
    - Maintains a chronological ledger of all operations per-account and globally.
    - Thread-safe for concurrent operations within a single process.
    """

    def __init__(self, decimal_places: int = 2, rounding=ROUND_HALF_EVEN) -> None:
        if decimal_places < 0:
            raise ValueError("decimal_places must be non-negative")
        # Quantization unit, e.g., 2 -> Decimal('0.01')
        self._quant: Decimal = Decimal(10) ** (-decimal_places)
        self._rounding = rounding

        self._accounts: Dict[str, Account] = {}
        self._ledger: List[LedgerEntry] = []
        self._per_account_ledger: Dict[str, List[LedgerEntry]] = {}
        self._lock = threading.RLock()

    # ---------------------------- Public API ----------------------------
    def create_account(
        self,
        account_id: Optional[str] = None,
        initial_balance: Union[Decimal, int, float, str] = 0,
        memo: Optional[str] = None,
    ) -> str:
        """
        Create a new account with an optional initial balance.

        Args:
            account_id: Optional explicit account identifier. If None, a UUID4 hex is generated.
            initial_balance: Non-negative initial balance. Defaults to 0.
            memo: Optional note to include in the creation ledger entry.

        Returns:
            The account identifier.

        Raises:
            AccountAlreadyExistsError: If the specified account_id already exists.
            InvalidAmountError: If initial_balance is negative or not a valid amount.
        """
        with self._lock:
            aid = account_id or uuid.uuid4().hex
            if aid in self._accounts:
                raise AccountAlreadyExistsError(f"Account '{aid}' already exists")

            amount = self._to_decimal(initial_balance)
            if amount < Decimal(0):
                raise InvalidAmountError("Initial balance cannot be negative")

            now = datetime.now(timezone.utc)
            account = Account(id=aid, balance=amount, created_at=now)
            self._accounts[aid] = account
            self._per_account_ledger[aid] = []

            # Log creation (amount may be zero)
            self._log(
                account_id=aid,
                type_="create",
                amount=amount,
                balance_after=amount,
                memo=memo,
                timestamp=now,
            )
            return aid

    def deposit(self, account_id: str, amount: Union[Decimal, int, float, str], memo: Optional[str] = None) -> Decimal:
        """
        Deposit a positive amount into the specified account.

        Args:
            account_id: The account identifier.
            amount: The amount to deposit (must be > 0).
            memo: Optional note to include in the ledger entry.

        Returns:
            The new balance as a Decimal.

        Raises:
            AccountNotFoundError: If the account does not exist.
            InvalidAmountError: If amount is not valid or not strictly positive.
        """
        with self._lock:
            account = self._get_account(account_id)
            dec_amount = self._to_decimal(amount)
            if dec_amount <= Decimal(0):
                raise InvalidAmountError("Deposit amount must be greater than zero")

            new_balance = (account.balance + dec_amount).quantize(self._quant, rounding=self._rounding)
            account.balance = new_balance

            self._log(
                account_id=account_id,
                type_="deposit",
                amount=dec_amount,
                balance_after=new_balance,
                memo=memo,
            )
            return new_balance

    def withdraw(self, account_id: str, amount: Union[Decimal, int, float, str], memo: Optional[str] = None) -> Decimal:
        """
        Withdraw a positive amount from the specified account.

        Args:
            account_id: The account identifier.
            amount: The amount to withdraw (must be > 0 and <= balance).
            memo: Optional note to include in the ledger entry.

        Returns:
            The new balance as a Decimal.

        Raises:
            AccountNotFoundError: If the account does not exist.
            InvalidAmountError: If amount is not valid or not strictly positive.
            InsufficientFundsError: If the amount exceeds the available balance.
        """
        with self._lock:
            account = self._get_account(account_id)
            dec_amount = self._to_decimal(amount)
            if dec_amount <= Decimal(0):
                raise InvalidAmountError("Withdrawal amount must be greater than zero")
            if dec_amount > account.balance:
                raise InsufficientFundsError("Insufficient funds for withdrawal")

            new_balance = (account.balance - dec_amount).quantize(self._quant, rounding=self._rounding)
            account.balance = new_balance

            self._log(
                account_id=account_id,
                type_="withdrawal",
                amount=dec_amount,
                balance_after=new_balance,
                memo=memo,
            )
            return new_balance

    def get_balance(self, account_id: str) -> Decimal:
        """Return the current balance of the specified account."""
        with self._lock:
            account = self._get_account(account_id)
            return account.balance

    def get_ledger(self, account_id: Optional[str] = None) -> List[LedgerEntry]:
        """
        Retrieve the ledger entries.

        Args:
            account_id: If provided, returns entries for that account only. Otherwise, returns all entries.

        Returns:
            A new list of LedgerEntry instances in chronological order.

        Raises:
            AccountNotFoundError: If account_id is provided but the account does not exist.
        """
        with self._lock:
            if account_id is None:
                return list(self._ledger)
            # Validate account exists
            self._get_account(account_id)
            return list(self._per_account_ledger.get(account_id, []))

    def list_accounts(self) -> List[str]:
        """Return a list of all account IDs."""
        with self._lock:
            return list(self._accounts.keys())

    # --------------------------- Internal Utils ---------------------------
    def _to_decimal(self, value: Union[Decimal, int, float, str]) -> Decimal:
        """Convert a numeric value to a quantized Decimal using the service's precision and rounding."""
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
                raise InvalidAmountError(f"Unsupported amount type: {type(value)!r}")
            return dec.quantize(self._quant, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidAmountError("Invalid monetary amount") from exc

    def _get_account(self, account_id: str) -> Account:
        account = self._accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account '{account_id}' not found")
        return account

    def _log(
        self,
        account_id: str,
        type_: str,
        amount: Decimal,
        balance_after: Decimal,
        memo: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        entry = LedgerEntry(
            timestamp=timestamp or datetime.now(timezone.utc),
            account_id=account_id,
            type=type_,
            amount=amount,
            balance_after=balance_after,
            memo=memo,
        )
        self._ledger.append(entry)
        self._per_account_ledger.setdefault(account_id, []).append(entry)