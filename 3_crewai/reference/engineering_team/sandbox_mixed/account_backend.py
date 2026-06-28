from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Any
import uuid


class AccountError(Exception):
    pass


class AccountNotFoundError(AccountError):
    pass


class ValidationError(AccountError):
    pass


class InsufficientFundsError(AccountError):
    pass


class InsufficientSharesError(AccountError):
    pass


class UnknownSymbolError(AccountError):
    pass


class TransactionType(str, Enum):
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    account_id: str
    transaction_type: TransactionType
    timestamp: datetime
    amount: float = 0.0
    symbol: Optional[str] = None
    quantity: int = 0
    share_price: Optional[float] = None
    notes: str = ""


@dataclass
class Account:
    account_id: str
    owner_name: str
    created_at: datetime
    initial_deposit: float
    cash_balance: float
    holdings: dict[str, int]
    transaction_ids: list[int]


def get_share_price(symbol: str) -> float:
    normalized = symbol.upper()
    prices = {
        "AAPL": 150.00,
        "TSLA": 250.00,
        "GOOGL": 2800.00,
    }
    if normalized not in prices:
        raise UnknownSymbolError(f"Unknown symbol: {symbol}")
    return prices[normalized]


class AccountService:
    def __init__(
        self,
        price_provider: Callable[[str], float] = get_share_price,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._accounts: dict[str, Account] = {}
        self._transactions: list[Transaction] = []
        self._next_transaction_id: int = 1
        self._price_provider: Callable[[str], float] = price_provider
        self._clock: Callable[[], datetime] = clock if clock else datetime.now

    def _now(self) -> datetime:
        return self._clock()

    def _generate_account_id(self) -> str:
        return str(uuid.uuid4())

    def _next_id(self) -> int:
        idx = self._next_transaction_id
        self._next_transaction_id += 1
        return idx

    def _record_transaction(
        self,
        account_id: str,
        transaction_type: TransactionType,
        amount: float = 0.0,
        symbol: Optional[str] = None,
        quantity: int = 0,
        share_price: Optional[float] = None,
        notes: str = "",
    ) -> Transaction:
        tx = Transaction(
            transaction_id=self._next_id(),
            account_id=account_id,
            transaction_type=transaction_type,
            timestamp=self._now(),
            amount=amount,
            symbol=symbol,
            quantity=quantity,
            share_price=share_price,
            notes=notes,
        )
        self._transactions.append(tx)
        return tx

    def _validate_positive_amount(self, amount: float, field_name: str = "amount") -> None:
        if amount <= 0:
            raise ValidationError(f"{field_name} must be greater than zero.")

    def _validate_positive_quantity(self, quantity: int) -> int:
        if isinstance(quantity, bool):
            raise ValidationError("Quantity must be a positive whole-number integer.")
        if isinstance(quantity, float):
            if not quantity.is_integer():
                raise ValidationError("Quantity must be a positive whole-number integer.")
            quantity = int(quantity)
        elif not isinstance(quantity, int):
            raise ValidationError("Quantity must be a positive whole-number integer.")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return quantity

    def _normalize_symbol(self, symbol: str) -> str:
        if not symbol:
            raise ValidationError("Symbol cannot be empty.")
        return symbol.upper()

    def _transactions_for_account(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> list[Transaction]:
        txs = []
        for tx in self._transactions:
            if tx.account_id == account_id:
                if as_of is None or tx.timestamp <= as_of:
                    txs.append(tx)
        return txs

    def create_account(self, owner_name: str, initial_deposit: float = 0.0) -> Account:
        if not owner_name:
            raise ValidationError("Owner name cannot be empty.")
        if initial_deposit < 0:
            raise ValidationError("Initial deposit cannot be negative.")

        account_id = self._generate_account_id()
        created_at = self._now()

        tx = self._record_transaction(
            account_id=account_id,
            transaction_type=TransactionType.CREATE_ACCOUNT,
            amount=initial_deposit,
            notes="Account created",
        )

        account = Account(
            account_id=account_id,
            owner_name=owner_name,
            created_at=created_at,
            initial_deposit=initial_deposit,
            cash_balance=initial_deposit,
            holdings={},
            transaction_ids=[tx.transaction_id],
        )
        self._accounts[account_id] = account
        return account

    def get_account(self, account_id: str) -> Account:
        if account_id not in self._accounts:
            raise AccountNotFoundError(f"Account {account_id} not found.")
        return self._accounts[account_id]

    def list_accounts(self) -> list[Account]:
        return list(self._accounts.values())

    def deposit(self, account_id: str, amount: float) -> Account:
        account = self.get_account(account_id)
        self._validate_positive_amount(amount, "Deposit amount")

        tx = self._record_transaction(
            account_id=account_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            notes="Deposit funds",
        )
        account.cash_balance += amount
        account.transaction_ids.append(tx.transaction_id)
        return account

    def withdraw(self, account_id: str, amount: float) -> Account:
        account = self.get_account(account_id)
        self._validate_positive_amount(amount, "Withdrawal amount")

        if account.cash_balance - amount < 0:
            raise InsufficientFundsError("Insufficient funds for withdrawal.")

        tx = self._record_transaction(
            account_id=account_id,
            transaction_type=TransactionType.WITHDRAW,
            amount=amount,
            notes="Withdraw funds",
        )
        account.cash_balance -= amount
        account.transaction_ids.append(tx.transaction_id)
        return account

    def buy(self, account_id: str, symbol: str, quantity: int) -> Account:
        account = self.get_account(account_id)
        normalized_symbol = self._normalize_symbol(symbol)
        quantity = self._validate_positive_quantity(quantity)
        price = self._price_provider(normalized_symbol)
        cost = price * quantity

        if account.cash_balance < cost:
            raise InsufficientFundsError("Insufficient funds for purchase.")

        tx = self._record_transaction(
            account_id=account_id,
            transaction_type=TransactionType.BUY,
            amount=cost,
            symbol=normalized_symbol,
            quantity=quantity,
            share_price=price,
            notes=f"Buy {quantity} shares of {normalized_symbol}",
        )

        account.cash_balance -= cost
        account.holdings[normalized_symbol] = account.holdings.get(normalized_symbol, 0) + quantity
        account.transaction_ids.append(tx.transaction_id)
        return account

    def sell(self, account_id: str, symbol: str, quantity: int) -> Account:
        account = self.get_account(account_id)
        normalized_symbol = self._normalize_symbol(symbol)
        quantity = self._validate_positive_quantity(quantity)
        price = self._price_provider(normalized_symbol)

        current_quantity = account.holdings.get(normalized_symbol, 0)
        if current_quantity < quantity:
            raise InsufficientSharesError("Insufficient shares for sale.")

        proceeds = price * quantity

        tx = self._record_transaction(
            account_id=account_id,
            transaction_type=TransactionType.SELL,
            amount=proceeds,
            symbol=normalized_symbol,
            quantity=quantity,
            share_price=price,
            notes=f"Sell {quantity} shares of {normalized_symbol}",
        )

        account.cash_balance += proceeds
        account.holdings[normalized_symbol] -= quantity
        if account.holdings[normalized_symbol] == 0:
            del account.holdings[normalized_symbol]

        account.transaction_ids.append(tx.transaction_id)
        return account

    def get_holdings(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> dict[str, int]:
        self.get_account(account_id)

        if as_of is None:
            account = self.get_account(account_id)
            return dict(account.holdings)

        txs = self._transactions_for_account(account_id, as_of)
        holdings: dict[str, int] = {}
        for tx in txs:
            if tx.transaction_type == TransactionType.BUY and tx.symbol:
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) + tx.quantity
            elif tx.transaction_type == TransactionType.SELL and tx.symbol:
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) - tx.quantity
                if holdings[tx.symbol] == 0:
                    del holdings[tx.symbol]

        return holdings

    def get_cash_balance(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        self.get_account(account_id)

        if as_of is None:
            account = self.get_account(account_id)
            return account.cash_balance

        txs = self._transactions_for_account(account_id, as_of)
        balance = 0.0
        for tx in txs:
            if tx.transaction_type == TransactionType.CREATE_ACCOUNT:
                balance += tx.amount
            elif tx.transaction_type == TransactionType.DEPOSIT:
                balance += tx.amount
            elif tx.transaction_type == TransactionType.WITHDRAW:
                balance -= tx.amount
            elif tx.transaction_type == TransactionType.BUY:
                balance -= tx.amount
            elif tx.transaction_type == TransactionType.SELL:
                balance += tx.amount

        return balance

    def get_portfolio_value(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        cash = self.get_cash_balance(account_id, as_of)
        holdings = self.get_holdings(account_id, as_of)

        holdings_value = 0.0
        for sym, qty in holdings.items():
            holdings_value += qty * self._price_provider(sym)

        return cash + holdings_value

    def get_total_deposits(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        self.get_account(account_id)
        txs = self._transactions_for_account(account_id, as_of)
        total = 0.0
        for tx in txs:
            if tx.transaction_type in (TransactionType.CREATE_ACCOUNT, TransactionType.DEPOSIT):
                total += tx.amount
        return total

    def get_total_withdrawals(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        self.get_account(account_id)
        txs = self._transactions_for_account(account_id, as_of)
        total = 0.0
        for tx in txs:
            if tx.transaction_type == TransactionType.WITHDRAW:
                total += tx.amount
        return total

    def get_net_contributions(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        self.get_account(account_id)
        return self.get_total_deposits(account_id, as_of) - self.get_total_withdrawals(account_id, as_of)

    def get_profit_loss(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        portfolio_val = self.get_portfolio_value(account_id, as_of)
        net_contribs = self.get_net_contributions(account_id, as_of)
        return portfolio_val - net_contribs

    def get_account_summary(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> dict[str, Any]:
        account = self.get_account(account_id)
        cash = self.get_cash_balance(account_id, as_of)
        holdings = self.get_holdings(account_id, as_of)
        portfolio_val = self.get_portfolio_value(account_id, as_of)
        holdings_market_value = portfolio_val - cash

        return {
            "account_id": account.account_id,
            "owner_name": account.owner_name,
            "created_at": account.created_at,
            "cash_balance": cash,
            "holdings": holdings,
            "holdings_market_value": holdings_market_value,
            "portfolio_value": portfolio_val,
            "initial_deposit": account.initial_deposit,
            "total_deposits": self.get_total_deposits(account_id, as_of),
            "total_withdrawals": self.get_total_withdrawals(account_id, as_of),
            "net_contributions": self.get_net_contributions(account_id, as_of),
            "profit_loss": self.get_profit_loss(account_id, as_of),
        }

    def list_transactions(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> list[Transaction]:
        self.get_account(account_id)
        txs = self._transactions_for_account(account_id, as_of)
        txs.sort(key=lambda t: (t.timestamp, t.transaction_id))
        return txs

    def list_transactions_as_dicts(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        txs = self.list_transactions(account_id, as_of)
        out = []
        for tx in txs:
            out.append({
                "ID": tx.transaction_id,
                "Timestamp": tx.timestamp.isoformat(),
                "Type": tx.transaction_type.value,
                "Symbol": tx.symbol if tx.symbol else "",
                "Quantity": tx.quantity if tx.quantity else 0,
                "Share Price": tx.share_price if tx.share_price else 0.0,
                "Amount": tx.amount,
                "Notes": tx.notes,
            })
        return out

    def list_holdings_as_dicts(
        self,
        account_id: str,
        as_of: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        holdings = self.get_holdings(account_id, as_of)
        out = []
        for sym, qty in holdings.items():
            price = self._price_provider(sym)
            out.append({
                "Symbol": sym,
                "Quantity": qty,
                "Current Price": price,
                "Market Value": qty * price,
            })
        return out
