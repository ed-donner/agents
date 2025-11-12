import decimal
import time
from typing import Dict, List, TypedDict, Optional, Callable
from enum import Enum

# --- CONFIGURATION / EXTERNAL DEPENDENCY MOCK ---

FIXED_PRICES: Dict[str, decimal.Decimal] = {
    'AAPL': decimal.Decimal('150.0000'),
    'TSLA': decimal.Decimal('195.0000'),
    'GOOGL': decimal.Decimal('130.0000'),
    'MSFT': decimal.Decimal('300.5000'),
    'AMD': decimal.Decimal('100.0000'),
    'XOM': decimal.Decimal('500.0000')
}

PRICE_PRECISION = decimal.Decimal('0.0000')

def get_share_price(symbol: str) -> decimal.Decimal:
    """
    Simulates retrieving the current market price for a given stock symbol.
    
    This implementation uses fixed prices for testing (D-1).

    Args:
        symbol: The ticker symbol (case insensitive).

    Returns:
        The price as a Decimal rounded to 4 places.

    Raises:
        InvalidSymbol: If the symbol is not found in the fixed price list (FR-3.3).
    """
    price = FIXED_PRICES.get(symbol.upper())
    if price is None:
        raise InvalidSymbol(f"Invalid or unsupported share symbol: {symbol}")
    return price.quantize(PRICE_PRECISION)

# --- CUSTOM EXCEPTIONS ---

class AccountError(Exception):
    """Base exception for account management issues."""
    pass

class InsufficientFunds(AccountError):
    """Raised when a withdrawal or purchase exceeds the available cash balance (FR-2.2, FR-3.2)."""
    pass

class InsufficientHoldings(AccountError):
    """Raised when a user attempts to sell more shares than they possess (FR-4.2)."""
    pass

class InvalidSymbol(AccountError):
    """Raised when an unsupported or invalid stock symbol is used (FR-3.3)."""
    pass

class InvalidAmount(AccountError):
    """Raised when a transaction amount or quantity is zero or negative (FR-2.3)."""
    pass

# --- DATA MODELS ---

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"

class TransactionRecord(TypedDict):
    """Schema for a single logged transaction (FR-2.4, FR-3.4, FR-4.3)."""
    id: int
    timestamp: float
    type: TransactionType
    symbol: Optional[str]
    quantity: Optional[decimal.Decimal]
    price: Optional[decimal.Decimal]
    amount: decimal.Decimal # Cash impact (positive for credit, negative for debit)
    details: str

class HoldingDetail(TypedDict):
    """Schema for an item in the holdings report (FR-5.4)."""
    symbol: str
    quantity: decimal.Decimal
    current_price: decimal.Decimal
    market_value: decimal.Decimal

class PortfolioSummary(TypedDict):
    """Schema for the overall portfolio summary (FR-5.1, FR-5.2)."""
    cash_balance: decimal.Decimal
    total_market_value: decimal.Decimal
    total_portfolio_value: decimal.Decimal
    total_deposits_baseline: decimal.Decimal
    profit_loss: decimal.Decimal

# --- CORE CLASS IMPLEMENTATION ---

class Account:
    """
    Manages a user's cash balance, share holdings, and transaction history 
    for a trading simulation. 
    
    All financial attributes are stored using decimal.Decimal (NFR-1.1).
    """

    def __init__(self, user_id: str):
        """
        Initializes a new trading simulation account (FR-1.1).

        Args:
            user_id: A unique identifier for the user.
        """
        self.user_id: str = user_id
        self._ZERO: decimal.Decimal = decimal.Decimal('0.0000')
        self.cash_balance: decimal.Decimal = self._ZERO
        self.holdings: Dict[str, decimal.Decimal] = {}  # {SYMBOL: QUANTITY}
        self.transactions: List[TransactionRecord] = []
        self.deposits_baseline: decimal.Decimal = self._ZERO
        self._transaction_counter: int = 0

    def _validate_positive_amount(self, amount: decimal.Decimal, is_quantity: bool = False) -> None:
        """Helper to ensure amount/quantity is positive (FR-2.3 equivalent)."""
        if amount <= self._ZERO:
            msg = "Quantity must be positive." if is_quantity else "Amount must be positive."
            raise InvalidAmount(msg)

    def _log_transaction(
        self,
        tx_type: TransactionType,
        amount_impact: decimal.Decimal,
        details: str,
        symbol: Optional[str] = None,
        quantity: Optional[decimal.Decimal] = None,
        price: Optional[decimal.Decimal] = None
    ) -> None:
        """Records a transaction into the history (FR-2.4, FR-3.4, FR-4.3)."""
        self._transaction_counter += 1
        record: TransactionRecord = {
            'id': self._transaction_counter,
            'timestamp': time.time(),
            'type': tx_type,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': amount_impact.quantize(PRICE_PRECISION),
            'details': details
        }
        self.transactions.append(record)

    def deposit(self, amount: decimal.Decimal) -> None:
        """
        Adds funds to the cash balance and tracks the total deposits baseline.

        Args:
            amount: The positive amount to deposit.

        Raises:
            InvalidAmount: If amount is less than or equal to zero.
        """
        amount = amount.quantize(PRICE_PRECISION)
        self._validate_positive_amount(amount)

        self.cash_balance += amount
        self.deposits_baseline += amount # FR-5.3

        self._log_transaction(
            tx_type=TransactionType.DEPOSIT,
            amount_impact=amount,
            details=f"Deposit of {amount}",
        )

    def withdraw(self, amount: decimal.Decimal) -> None:
        """
        Withdraws funds from the cash balance. Prevents overdraft (FR-2.2).

        Args:
            amount: The positive amount to withdraw.

        Raises:
            InvalidAmount: If amount is less than or equal to zero (FR-2.3).
            InsufficientFunds: If withdrawal exceeds current balance (FR-2.2).
        """
        amount = amount.quantize(PRICE_PRECISION)
        self._validate_positive_amount(amount)

        if amount > self.cash_balance:
            raise InsufficientFunds("Insufficient funds") # Required error message

        self.cash_balance -= amount

        self._log_transaction(
            tx_type=TransactionType.WITHDRAWAL,
            amount_impact=-amount,
            details=f"Withdrawal of {amount}",
        )

    def buy_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        """
        Executes a buy order (FR-3.1). Debits cash and credits holdings. 
        Enforces affordability (FR-3.2).

        Args:
            symbol: The ticker symbol of the share.
            quantity: The number of shares to buy.

        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved (FR-3.3).
            InsufficientFunds: If total cost exceeds cash balance (FR-3.2).
        """
        symbol = symbol.upper()
        quantity = quantity.quantize(PRICE_PRECISION)
        self._validate_positive_amount(quantity, is_quantity=True)

        # Price retrieval handles InvalidSymbol check (FR-3.3)
        price = get_share_price(symbol)
        total_cost = (price * quantity).quantize(PRICE_PRECISION)

        if total_cost > self.cash_balance:
            raise InsufficientFunds(
                "Insufficient funds to cover trade cost"
            ) # Required error message

        # Update state
        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, self._ZERO) + quantity

        self._log_transaction(
            tx_type=TransactionType.BUY,
            amount_impact=-total_cost,
            details=f"Bought {quantity} of {symbol} @ {price}",
            symbol=symbol,
            quantity=quantity,
            price=price
        )

    def sell_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        """
        Executes a sell order (FR-4.1). Credits cash and debits holdings. 
        Enforces possession (FR-4.2).

        Args:
            symbol: The ticker symbol of the share.
            quantity: The number of shares to sell.

        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved (FR-4.4).
            InsufficientHoldings: If user attempts to sell more than they possess (FR-4.2).
        """
        symbol = symbol.upper()
        quantity = quantity.quantize(PRICE_PRECISION)
        self._validate_positive_amount(quantity, is_quantity=True)

        current_holding = self.holdings.get(symbol, self._ZERO)
        if quantity > current_holding:
            raise InsufficientHoldings(
                f"Insufficient holdings for {symbol}"
            ) # Required error message template

        # Price retrieval handles InvalidSymbol check (FR-4.4)
        price = get_share_price(symbol)
        total_proceeds = (price * quantity).quantize(PRICE_PRECISION)

        # Update state
        self.cash_balance += total_proceeds
        
        new_holding = current_holding - quantity
        if new_holding <= self._ZERO:
            del self.holdings[symbol]
        else:
            self.holdings[symbol] = new_holding

        self._log_transaction(
            tx_type=TransactionType.SELL,
            amount_impact=total_proceeds,
            details=f"Sold {quantity} of {symbol} @ {price}",
            symbol=symbol,
            quantity=quantity,
            price=price
        )

    def get_transaction_history(self) -> List[TransactionRecord]:
        """Returns the full chronological list of all transactions."""
        return self.transactions

    def get_holdings_report(self) -> Dict[str, HoldingDetail]:
        """
        Generates a detailed report of current share holdings including market value (FR-5.4).

        Returns:
            A dictionary mapping symbol to HoldingDetail.
        """
        report: Dict[str, HoldingDetail] = {}
        
        for symbol, quantity in self.holdings.items():
            if quantity <= self._ZERO:
                continue

            try:
                current_price = get_share_price(symbol)
            except InvalidSymbol:
                # Use zero value if price cannot be found, keeping calculation safe
                current_price = self._ZERO

            market_value = (quantity * current_price).quantize(PRICE_PRECISION)

            report[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'current_price': current_price,
                'market_value': market_value
            }
        
        return report

    def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Calculates and returns the Total Portfolio Value (TPV) and Profit/Loss (P&L) (FR-5.1, FR-5.2).

        Returns:
            A dictionary containing summary metrics.
        """
        holdings_report = self.get_holdings_report()
        
        # Calculate Total Market Value (TMV)
        total_market_value = sum(
            [detail['market_value'] for detail in holdings_report.values()],
            self._ZERO
        ).quantize(PRICE_PRECISION)

        # Calculate Total Portfolio Value (TPV) (FR-5.1)
        total_portfolio_value = (self.cash_balance + total_market_value).quantize(PRICE_PRECISION)

        # Calculate Profit/Loss (P&L) (FR-5.2)
        profit_loss = (total_portfolio_value - self.deposits_baseline).quantize(PRICE_PRECISION)

        return {
            'cash_balance': self.cash_balance,
            'total_market_value': total_market_value,
            'total_portfolio_value': total_portfolio_value,
            'total_deposits_baseline': self.deposits_baseline,
            'profit_loss': profit_loss
        }