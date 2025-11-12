"""
Trading Simulation Account Management Module

This module provides core account management, fund operations, and trading simulation
capabilities for a trading platform. It enforces critical financial constraints including
prevention of overdrafts and short-selling.

Key Features:
    - High-precision financial calculations using Decimal type
    - Comprehensive transaction history tracking
    - Real-time portfolio valuation and P&L reporting
    - Strict enforcement of financial constraints

Usage Example:
    from accounts import Account
    from decimal import Decimal
    
    # Create account and deposit funds
    account = Account("user_123")
    account.deposit(Decimal('5000.00'))
    
    # Execute trades
    account.buy_shares('AAPL', Decimal('10'))
    account.sell_shares('AAPL', Decimal('5'))
    
    # Get portfolio summary
    summary = account.get_portfolio_summary()
    print(f"Total Value: ${summary['total_portfolio_value']}")
    print(f"P&L: ${summary['profit_loss']}")
"""

import uuid
import time
from decimal import Decimal
from typing import Dict, List, Optional
from enum import Enum


class AccountError(Exception):
    """Base exception class for account-related errors."""
    pass


class InsufficientFunds(AccountError):
    """Raised when attempting to withdraw or purchase with insufficient cash balance."""
    pass


class InsufficientHoldings(AccountError):
    """Raised when attempting to sell shares that are not owned in sufficient quantity."""
    pass


class InvalidSymbol(AccountError):
    """Raised when an invalid or unsupported share symbol is referenced."""
    pass


class InvalidAmount(AccountError):
    """Raised when a transaction amount or quantity is invalid (e.g., zero or negative)."""
    pass


FIXED_PRICES = {
    'AAPL': Decimal('150.0000'),
    'TSLA': Decimal('195.0000'),
    'GOOGL': Decimal('130.0000'),
    'MSFT': Decimal('300.5000'),
    'AMD': Decimal('100.0000'),
    'XOM': Decimal('500.0000'),
    'XYZ': Decimal('100.0000'),
    'AMZN': Decimal('120.0000'),
    'NFLX': Decimal('500.0000')
}


def get_share_price(symbol: str) -> Decimal:
    """
    Simulates retrieving the current market price for a given stock symbol.
    
    This is a test implementation that returns fixed prices for supported symbols.
    In production, this would be replaced with a real market data API connector.
    
    Args:
        symbol: The ticker symbol (case insensitive).
    
    Returns:
        The price as a Decimal with 4 decimal places.
    
    Raises:
        InvalidSymbol: If the symbol is not found in the supported symbol list.
    """
    price = FIXED_PRICES.get(symbol.upper())
    if price is None:
        raise InvalidSymbol(f"Invalid or unsupported share symbol: {symbol}")
    return price


class TransactionType(Enum):
    """Enumeration of supported transaction types."""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"


class TransactionRecord(dict):
    """
    Schema for transaction records stored in account history.
    
    Attributes:
        id: Unique transaction identifier
        timestamp: Unix epoch time of transaction execution
        type: TransactionType enum value
        symbol: Stock symbol (for BUY/SELL transactions)
        quantity: Number of shares (for BUY/SELL transactions)
        price: Execution price per share (for BUY/SELL transactions)
        amount: Net cash impact (positive for credits, negative for debits)
        details: Human-readable transaction description
    """
    pass


class HoldingDetail(dict):
    """
    Schema for individual holding details in portfolio reports.
    
    Attributes:
        symbol: Stock ticker symbol
        quantity: Number of shares owned
        current_price: Current market price per share
        market_value: Total value (quantity * current_price)
    """
    pass


class PortfolioSummary(dict):
    """
    Schema for comprehensive portfolio summary reports.
    
    Attributes:
        cash_balance: Current available cash
        total_market_value: Sum of all holdings' market values
        total_portfolio_value: Cash + market value of all holdings
        total_deposits_baseline: Sum of all historical deposits
        profit_loss: Total portfolio value - total deposits baseline
    """
    pass


class Account:
    """
    Primary account management class for trading simulation platform.
    
    Manages user cash balance, share holdings, transaction history, and provides
    portfolio reporting capabilities. Enforces strict financial constraints to
    prevent overdrafts and short-selling.
    
    Attributes:
        user_id: Unique identifier for the account owner
        cash_balance: Current available cash (Decimal with 4 decimal places)
        holdings: Dictionary mapping stock symbols to quantities owned
        transactions: Chronological list of all account transactions
        deposits_baseline: Running sum of all deposits (for P&L calculation)
    """
    
    def __init__(self, user_id: str):
        """
        Initializes a new trading simulation account.
        
        Creates an account with zero cash balance, no holdings, and empty
        transaction history. The account is immediately ready for deposits
        and trading operations.
        
        Args:
            user_id: A unique identifier for the user. Uniqueness enforcement
                    is expected to be handled by the registration system.
        
        Note:
            Initial state satisfies FR-1.1 (zero balance) and FR-1.3 (empty history).
        """
        self.user_id: str = user_id
        self.cash_balance: Decimal = Decimal('0.0000')
        self.holdings: Dict[str, Decimal] = {}
        self.transactions: List[TransactionRecord] = []
        self.deposits_baseline: Decimal = Decimal('0.0000')
    
    def deposit(self, amount: Decimal) -> None:
        """
        Adds funds to the cash balance and tracks total deposits baseline.
        
        Increases the account's cash balance by the specified amount and updates
        the cumulative deposits baseline used for profit/loss calculations. All
        successful deposits are logged in the transaction history.
        
        Args:
            amount: The positive amount to deposit. Must use Decimal type with
                   up to 4 decimal places for precision.
        
        Raises:
            InvalidAmount: If amount is less than or equal to zero.
        
        Example:
            account.deposit(Decimal('1000.00'))
        """
        if amount <= 0:
            raise InvalidAmount("Amount must be positive")
        
        self.cash_balance += amount
        self.deposits_baseline += amount
        
        transaction = TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.DEPOSIT,
            'symbol': None,
            'quantity': None,
            'price': None,
            'amount': amount,
            'details': f"Deposit of ${amount}"
        })
        self.transactions.append(transaction)
    
    def withdraw(self, amount: Decimal) -> None:
        """
        Withdraws funds from the cash balance with overdraft prevention.
        
        Reduces the account's cash balance by the specified amount. Enforces
        the critical constraint that withdrawals cannot result in a negative
        balance, preventing overdrafts.
        
        Args:
            amount: The positive amount to withdraw. Must be a Decimal.
        
        Raises:
            InvalidAmount: If amount is less than or equal to zero.
            InsufficientFunds: If withdrawal would result in negative balance.
        
        Example:
            account.withdraw(Decimal('500.00'))
        """
        if amount <= 0:
            raise InvalidAmount("Amount must be positive")
        
        if amount > self.cash_balance:
            raise InsufficientFunds("Insufficient funds")
        
        self.cash_balance -= amount
        
        transaction = TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.WITHDRAWAL,
            'symbol': None,
            'quantity': None,
            'price': None,
            'amount': -amount,
            'details': f"Withdrawal of ${amount}"
        })
        self.transactions.append(transaction)
    
    def buy_shares(self, symbol: str, quantity: Decimal) -> None:
        """
        Executes a buy order with affordability check and balance update.
        
        Purchases the specified quantity of shares at the current market price.
        Debits the total cost from cash balance and credits the holdings.
        Enforces affordability constraint - transaction is rejected if total
        cost exceeds available cash.
        
        Args:
            symbol: The ticker symbol of the share (e.g., 'AAPL').
            quantity: The number of shares to buy. Must be positive Decimal.
        
        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved.
            InsufficientFunds: If total cost exceeds cash balance.
        
        Example:
            account.buy_shares('AAPL', Decimal('10'))
        """
        if quantity <= 0:
            raise InvalidAmount("Quantity must be positive")
        
        try:
            price = get_share_price(symbol)
        except InvalidSymbol:
            raise
        
        total_cost = price * quantity
        
        if total_cost > self.cash_balance:
            raise InsufficientFunds("Insufficient funds to cover trade cost")
        
        self.cash_balance -= total_cost
        
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity
        
        transaction = TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.BUY,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': -total_cost,
            'details': f"Bought {quantity} shares of {symbol} at ${price} per share"
        })
        self.transactions.append(transaction)
    
    def sell_shares(self, symbol: str, quantity: Decimal) -> None:
        """
        Executes a sell order with possession check and balance update.
        
        Sells the specified quantity of shares at the current market price.
        Credits the total proceeds to cash balance and debits the holdings.
        Enforces possession constraint - transaction is rejected if attempting
        to sell more shares than owned (prevents short selling).
        
        Args:
            symbol: The ticker symbol of the share.
            quantity: The number of shares to sell. Must be positive Decimal.
        
        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved.
            InsufficientHoldings: If attempting to sell more than owned.
        
        Example:
            account.sell_shares('AAPL', Decimal('5'))
        """
        if quantity <= 0:
            raise InvalidAmount("Quantity must be positive")
        
        current_holding = self.holdings.get(symbol, Decimal('0'))
        
        if quantity > current_holding:
            raise InsufficientHoldings(f"Insufficient holdings for {symbol}")
        
        try:
            price = get_share_price(symbol)
        except InvalidSymbol:
            raise
        
        total_proceeds = price * quantity
        
        self.cash_balance += total_proceeds
        
        self.holdings[symbol] -= quantity
        
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        
        transaction = TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.SELL,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': total_proceeds,
            'details': f"Sold {quantity} shares of {symbol} at ${price} per share"
        })
        self.transactions.append(transaction)
    
    def get_transaction_history(self) -> List[TransactionRecord]:
        """
        Returns the complete chronological transaction history.
        
        Provides access to all recorded transactions including deposits,
        withdrawals, buys, and sells. Each transaction includes full details
        such as timestamp, type, amounts, and execution prices.
        
        Returns:
            A list of TransactionRecord dictionaries in chronological order.
        
        Example:
            history = account.get_transaction_history()
            for tx in history:
                print(f"{tx['type'].value}: {tx['details']}")
        """
        return self.transactions
    
    def get_holdings_report(self) -> Dict[str, HoldingDetail]:
        """
        Generates a detailed report of current share holdings.
        
        Creates a comprehensive view of all owned shares including current
        quantity, real-time market price, and calculated market value for
        each position. Requires price lookup for each held symbol.
        
        Returns:
            Dictionary mapping stock symbols to HoldingDetail dictionaries
            containing quantity, current_price, and market_value.
        
        Example:
            report = account.get_holdings_report()
            for symbol, details in report.items():
                print(f"{symbol}: {details['quantity']} shares @ ${details['current_price']}")
        """
        report = {}
        
        for symbol, quantity in self.holdings.items():
            try:
                current_price = get_share_price(symbol)
                market_value = quantity * current_price
                
                report[symbol] = HoldingDetail({
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'market_value': market_value
                })
            except InvalidSymbol:
                continue
        
        return report
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Calculates and returns comprehensive portfolio metrics.
        
        Computes total portfolio value (cash + market value of all holdings)
        and profit/loss relative to total deposits baseline. P&L calculation
        reflects both realized and unrealized gains/losses based on current
        market prices.
        
        Returns:
            PortfolioSummary dictionary containing:
                - cash_balance: Current available cash
                - total_market_value: Sum of all holdings' market values
                - total_portfolio_value: Total account value
                - total_deposits_baseline: Cumulative deposits
                - profit_loss: Total value minus deposits
        
        Example:
            summary = account.get_portfolio_summary()
            print(f"Portfolio Value: ${summary['total_portfolio_value']}")
            print(f"P&L: ${summary['profit_loss']}")
        """
        holdings_report = self.get_holdings_report()
        
        total_market_value = Decimal('0.0000')
        for holding_detail in holdings_report.values():
            total_market_value += holding_detail['market_value']
        
        total_portfolio_value = self.cash_balance + total_market_value
        profit_loss = total_portfolio_value - self.deposits_baseline
        
        return PortfolioSummary({
            'cash_balance': self.cash_balance,
            'total_market_value': total_market_value,
            'total_portfolio_value': total_portfolio_value,
            'total_deposits_baseline': self.deposits_baseline,
            'profit_loss': profit_loss
        })
