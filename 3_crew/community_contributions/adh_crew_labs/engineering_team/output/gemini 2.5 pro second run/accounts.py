import datetime
from decimal import Decimal
from typing import Dict, List, NamedTuple, Optional

# Custom exceptions for clear error handling
class InsufficientFundsError(Exception):
    """Raised when an action cannot be completed due to lack of cash."""
    pass

class InsufficientSharesError(Exception):
    """Raised when trying to sell more shares than owned."""
    pass

class InvalidSymbolError(Exception):
    """Raised when a stock symbol is not found in the price source."""
    pass

class InvalidQuantityError(Exception):
    """Raised when a quantity less than or equal to zero is provided."""
    pass

def get_share_price(symbol: str) -> Decimal:
    """
    Retrieves the current market price for a given stock symbol.

    This is a mock implementation for simulation purposes.

    Args:
        symbol: The stock symbol (e.g., 'AAPL').

    Returns:
        The price of one share as a Decimal object.

    Raises:
        InvalidSymbolError: If the symbol is not recognized.
    """
    prices = {
        'AAPL': Decimal('150.00'),
        'TSLA': Decimal('200.00'),
        'GOOGL': Decimal('100.00')
    }
    price = prices.get(symbol.upper())
    if price is None:
        raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
    return price

class Transaction(NamedTuple):
    """
    Represents a single financial transaction in the account history.
    """
    timestamp: datetime.datetime
    type: str  # e.g., 'DEPOSIT', 'WITHDRAW', 'BUY', 'SELL'
    symbol: Optional[str]
    quantity: Optional[int]
    share_price: Optional[Decimal]
    total_value: Decimal

class Account:
    """
    Manages a user's trading account, including cash, holdings,
    and transaction history.
    """
    def __init__(self, user_id: str):
        """
        Initializes a new trading account.

        Args:
            user_id: A unique identifier for the user.
        """
        self.user_id: str = user_id
        self.cash: Decimal = Decimal('0.00')
        self.holdings: Dict[str, int] = {} # Maps symbol -> quantity
        self.transactions: List[Transaction] = []
        self._total_deposits: Decimal = Decimal('0.00')
        self._total_withdrawals: Decimal = Decimal('0.00')

    def deposit(self, amount: Decimal):
        """
        Adds funds to the account's cash balance.

        Args:
            amount: The amount of money to deposit.

        Raises:
            ValueError: If the amount is not a positive number.
        """
        if amount <= Decimal('0.00'):
            raise ValueError("Deposit amount must be greater than zero.")
        self.cash += amount
        self._total_deposits += amount
        transaction = Transaction(
            timestamp=datetime.datetime.now(),
            type='DEPOSIT',
            symbol=None,
            quantity=None,
            share_price=None,
            total_value=amount
        )
        self.transactions.insert(0, transaction)

    def withdraw(self, amount: Decimal):
        """
        Removes funds from the account's cash balance.

        Args:
            amount: The amount of money to withdraw.

        Raises:
            ValueError: If the amount is not a positive number.
            InsufficientFundsError: If the withdrawal amount exceeds the cash balance.
        """
        if amount <= Decimal('0.00'):
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self.cash:
            raise InsufficientFundsError("Withdrawal amount cannot exceed your cash balance.")
        self.cash -= amount
        self._total_withdrawals += amount
        transaction = Transaction(
            timestamp=datetime.datetime.now(),
            type='WITHDRAW',
            symbol=None,
            quantity=None,
            share_price=None,
            total_value=-amount
        )
        self.transactions.insert(0, transaction)

    def buy_shares(self, symbol: str, quantity: int):
        """
        Purchases a specified quantity of shares for a given stock symbol.

        Args:
            symbol: The stock symbol to buy (e.g., 'AAPL').
            quantity: The number of shares to purchase.

        Raises:
            InvalidQuantityError: If quantity is not greater than zero.
            InvalidSymbolError: If the stock symbol is not valid.
            InsufficientFundsError: If the total cost exceeds the cash balance.
        """
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be greater than zero.")
        
        symbol = symbol.upper()
        price = get_share_price(symbol)
        total_cost = price * quantity

        if total_cost > self.cash:
            raise InsufficientFundsError("Insufficient funds to complete this purchase.")

        self.cash -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        
        transaction = Transaction(
            timestamp=datetime.datetime.now(),
            type='BUY',
            symbol=symbol,
            quantity=quantity,
            share_price=price,
            total_value=-total_cost
        )
        self.transactions.insert(0, transaction)

    def sell_shares(self, symbol: str, quantity: int):
        """
        Sells a specified quantity of owned shares.

        Args:
            symbol: The stock symbol to sell.
            quantity: The number of shares to sell.

        Raises:
            InvalidQuantityError: If quantity is not greater than zero.
            InsufficientSharesError: If trying to sell more shares than owned.
        """
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be greater than zero.")
        
        symbol = symbol.upper()
        current_shares = self.holdings.get(symbol, 0)
        
        if current_shares == 0:
            raise InsufficientSharesError("You do not own any shares of this stock.")
        if quantity > current_shares:
            raise InsufficientSharesError("You do not have enough shares to sell.")

        price = get_share_price(symbol)
        total_sale_value = price * quantity

        self.cash += total_sale_value
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        transaction = Transaction(
            timestamp=datetime.datetime.now(),
            type='SELL',
            symbol=symbol,
            quantity=quantity,
            share_price=price,
            total_value=total_sale_value
        )
        self.transactions.insert(0, transaction)

    def get_holdings_value(self) -> Decimal:
        """
        Calculates the total market value of all shares currently held.

        Returns:
            The total value of all stock holdings as a Decimal.
        """
        total_value = Decimal('0.00')
        for symbol, quantity in self.holdings.items():
            try:
                total_value += get_share_price(symbol) * quantity
            except InvalidSymbolError:
                # In a real system, you might handle de-listed stocks differently.
                # For this simulation, we assume prices are always available for held stocks.
                pass
        return total_value

    def get_total_portfolio_value(self) -> Decimal:
        """
        Calculates the entire net worth of the account (cash + holdings).

        Returns:
            The total account value as a Decimal.
        """
        return self.cash + self.get_holdings_value()

    def get_profit_or_loss(self) -> Decimal:
        """
        Calculates the total profit or loss relative to the net amount deposited.

        Returns:
            The profit (positive) or loss (negative) as a Decimal.
        """
        net_deposits = self._total_deposits - self._total_withdrawals
        current_value = self.get_total_portfolio_value()
        return current_value - net_deposits

    def get_holdings_summary(self) -> Dict[str, Dict[str, object]]:
        """
        Provides a detailed summary of each holding.

        Returns:
            A dictionary where keys are stock symbols and values are details
            about that holding (quantity, current price, total value).
        """
        summary = {}
        for symbol, quantity in self.holdings.items():
            try:
                price = get_share_price(symbol)
                total_value = price * quantity
                summary[symbol] = {
                    'quantity': quantity,
                    'current_price': price,
                    'total_value': total_value
                }
            except InvalidSymbolError:
                pass
        return summary

    def get_transaction_history(self) -> List[Transaction]:
        """
        Returns a complete history of all transactions for the account.

        Returns:
            A list of Transaction namedtuples, in reverse chronological order.
        """
        return self.transactions.copy()