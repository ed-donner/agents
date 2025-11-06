import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

# Custom Exception Classes
class InsufficientFundsError(Exception):
    """Raised when user attempts transaction without sufficient cash balance"""
    pass

class InsufficientSharesError(Exception):
    """Raised when user attempts to sell more shares than owned"""
    pass

class InvalidSymbolError(Exception):
    """Raised when user attempts to trade invalid stock symbol"""
    pass

# Utility Functions
def validate_email(email: str) -> bool:
    """Validates email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def hash_password(password: str) -> str:
    """Hashes password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password_hash(password: str, hashed: str) -> bool:
    """Verifies password against hash"""
    return hash_password(password) == hashed

def get_share_price(symbol: str) -> float:
    """Test implementation that returns fixed prices for specific symbols"""
    prices = {
        'AAPL': 150.0,
        'TSLA': 200.0,
        'GOOGL': 100.0
    }
    if symbol not in prices:
        raise InvalidSymbolError(f"Stock symbol '{symbol}' not found.")
    return prices[symbol]

# Global registry to track existing email addresses
_existing_emails = set()

class Account:
    """Main account class for trading simulation platform"""
    
    def __init__(self, email: str, password: str) -> None:
        """Creates a new account with email and password"""
        if not validate_email(email):
            raise ValueError("Please enter a valid email address.")
        
        if email in _existing_emails:
            raise ValueError("This email address is already registered.")
        
        if not password:
            raise ValueError("Password cannot be empty.")
        
        self._email = email
        self._password_hash = hash_password(password)
        self._cash_balance = Decimal('0.0')
        self._holdings = {}  # symbol -> quantity
        self._transaction_history = []
        
        # Register this email as taken
        _existing_emails.add(email)
    
    def get_email(self) -> str:
        """Returns the account's email address"""
        return self._email
    
    def verify_password(self, password: str) -> bool:
        """Verifies if provided password matches account password"""
        return verify_password_hash(password, self._password_hash)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Changes account password after verifying old password"""
        if not self.verify_password(old_password):
            return False
        
        if not new_password:
            raise ValueError("New password cannot be empty.")
        
        self._password_hash = hash_password(new_password)
        return True
    
    def deposit(self, amount: float) -> None:
        """Deposits funds into the account"""
        if amount <= 0:
            if amount == 0:
                raise ValueError("Deposit amount must be greater than zero.")
            else:
                raise ValueError("Deposit amount must be a positive number.")
        
        amount_decimal = Decimal(str(amount))
        self._cash_balance += amount_decimal
        
        # Record transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'DEPOSIT',
            'amount': float(amount_decimal),
            'symbol': None,
            'quantity': None,
            'price': None,
            'total_value': float(amount_decimal)
        }
        self._transaction_history.append(transaction)
    
    def withdraw(self, amount: float) -> None:
        """Withdraws funds from the account"""
        if amount <= 0:
            if amount == 0:
                raise ValueError("Withdrawal amount must be greater than zero.")
            else:
                raise ValueError("Withdrawal amount must be a positive number.")
        
        amount_decimal = Decimal(str(amount))
        
        if self._cash_balance < amount_decimal:
            raise InsufficientFundsError("Insufficient funds to complete this transaction.")
        
        self._cash_balance -= amount_decimal
        
        # Record transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'WITHDRAWAL',
            'amount': float(amount_decimal),
            'symbol': None,
            'quantity': None,
            'price': None,
            'total_value': float(amount_decimal)
        }
        self._transaction_history.append(transaction)
    
    def get_cash_balance(self) -> float:
        """Returns current cash balance"""
        return float(self._cash_balance)
    
    def buy_shares(self, symbol: str, quantity: int) -> None:
        """Purchases shares of a stock"""
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
        
        try:
            price = get_share_price(symbol)
        except InvalidSymbolError:
            raise
        
        total_cost = Decimal(str(price * quantity))
        
        if self._cash_balance < total_cost:
            raise InsufficientFundsError("Insufficient funds to complete this transaction.")
        
        # Execute trade
        self._cash_balance -= total_cost
        self._holdings[symbol] = self._holdings.get(symbol, 0) + quantity
        
        # Record transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'BUY',
            'amount': None,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_value': float(total_cost)
        }
        self._transaction_history.append(transaction)
    
    def sell_shares(self, symbol: str, quantity: int) -> None:
        """Sells shares of a stock"""
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
        
        if symbol not in self._holdings or self._holdings[symbol] < quantity:
            raise InsufficientSharesError(f"Insufficient shares to complete this transaction.")
        
        try:
            price = get_share_price(symbol)
        except InvalidSymbolError:
            raise
        
        total_value = Decimal(str(price * quantity))
        
        # Execute trade
        self._cash_balance += total_value
        self._holdings[symbol] -= quantity
        
        # Remove symbol if no shares left
        if self._holdings[symbol] == 0:
            del self._holdings[symbol]
        
        # Record transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'SELL',
            'amount': None,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_value': float(total_value)
        }
        self._transaction_history.append(transaction)
    
    def get_holdings(self) -> Dict[str, int]:
        """Returns current stock holdings"""
        return self._holdings.copy()
    
    def get_holdings_value(self) -> float:
        """Calculates current market value of all holdings"""
        total_value = Decimal('0.0')
        
        for symbol, quantity in self._holdings.items():
            try:
                price = get_share_price(symbol)
                total_value += Decimal(str(price * quantity))
            except InvalidSymbolError:
                # If symbol is no longer valid, treat as $0 value
                continue
        
        return float(total_value)
    
    def get_portfolio_value(self) -> float:
        """Calculates total portfolio value (holdings + cash)"""
        return self.get_holdings_value() + self.get_cash_balance()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Returns comprehensive portfolio summary"""
        holdings_detail = {}
        
        for symbol, quantity in self._holdings.items():
            try:
                price = get_share_price(symbol)
                current_value = price * quantity
                holdings_detail[symbol] = {
                    'quantity': quantity,
                    'current_price': price,
                    'current_value': current_value
                }
            except InvalidSymbolError:
                holdings_detail[symbol] = {
                    'quantity': quantity,
                    'current_price': 0.0,
                    'current_value': 0.0
                }
        
        return {
            'holdings': holdings_detail,
            'total_holdings_value': self.get_holdings_value(),
            'cash_balance': self.get_cash_balance(),
            'total_portfolio_value': self.get_portfolio_value()
        }
    
    def get_total_deposits(self) -> float:
        """Calculates total amount deposited over account lifetime"""
        total = Decimal('0.0')
        for transaction in self._transaction_history:
            if transaction['type'] == 'DEPOSIT':
                total += Decimal(str(transaction['amount']))
        return float(total)
    
    def get_total_withdrawals(self) -> float:
        """Calculates total amount withdrawn over account lifetime"""
        total = Decimal('0.0')
        for transaction in self._transaction_history:
            if transaction['type'] == 'WITHDRAWAL':
                total += Decimal(str(transaction['amount']))
        return float(total)
    
    def get_profit_loss(self) -> float:
        """Calculates total profit/loss since account creation"""
        current_value = self.get_portfolio_value()
        total_deposits = self.get_total_deposits()
        total_withdrawals = self.get_total_withdrawals()
        
        return current_value - total_deposits + total_withdrawals
    
    def get_transaction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns transaction history in chronological order (newest first)"""
        history = sorted(self._transaction_history, key=lambda x: x['timestamp'], reverse=True)
        
        if limit is not None:
            history = history[:limit]
        
        return history
    
    def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
        """Returns filtered transaction history by type"""
        return [t for t in self._transaction_history if t['type'] == transaction_type]