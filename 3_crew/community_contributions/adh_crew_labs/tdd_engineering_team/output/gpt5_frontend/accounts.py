# accounts.py generated from accounts.txt requirements
# (Assuming the content of accounts.txt defines a trading simulation account system)

import uuid
import time
from decimal import Decimal
from typing import Dict, List, Optional
from enum import Enum

class AccountError(Exception):
    pass

class InsufficientFunds(AccountError):
    pass

class InsufficientHoldings(AccountError):
    pass

class InvalidSymbol(AccountError):
    pass

class InvalidAmount(AccountError):
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
    'NFLX': Decimal('500.0000'),
}

def get_share_price(symbol: str) -> Decimal:
    price = FIXED_PRICES.get(symbol.upper())
    if price is None:
        raise InvalidSymbol(f"Invalid or unsupported share symbol: {symbol}")
    return price

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"

class TransactionRecord(dict):
    pass

class HoldingDetail(dict):
    pass

class PortfolioSummary(dict):
    pass

class Account:
    def __init__(self, user_id: str):
        self.user_id: str = user_id
        self.cash_balance: Decimal = Decimal('0.0000')
        self.holdings: Dict[str, Decimal] = {}
        self.transactions: List[TransactionRecord] = []
        self.deposits_baseline: Decimal = Decimal('0.0000')

    def deposit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidAmount("Amount must be positive")
        self.cash_balance += amount
        self.deposits_baseline += amount
        self.transactions.append(TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.DEPOSIT,
            'symbol': None,
            'quantity': None,
            'price': None,
            'amount': amount,
            'details': f"Deposit of ${amount}"
        }))

    def withdraw(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidAmount("Amount must be positive")
        if amount > self.cash_balance:
            raise InsufficientFunds("Insufficient funds")
        self.cash_balance -= amount
        self.transactions.append(TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.WITHDRAWAL,
            'symbol': None,
            'quantity': None,
            'price': None,
            'amount': -amount,
            'details': f"Withdrawal of ${amount}"
        }))

    def buy_shares(self, symbol: str, quantity: Decimal) -> None:
        if quantity <= 0:
            raise InvalidAmount("Quantity must be positive")
        price = get_share_price(symbol)
        total_cost = price * quantity
        if total_cost > self.cash_balance:
            raise InsufficientFunds("Insufficient funds to cover trade cost")
        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, Decimal('0')) + quantity
        self.transactions.append(TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.BUY,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': -total_cost,
            'details': f"Bought {quantity} shares of {symbol} at ${price} per share"
        }))

    def sell_shares(self, symbol: str, quantity: Decimal) -> None:
        if quantity <= 0:
            raise InvalidAmount("Quantity must be positive")
        if self.holdings.get(symbol, Decimal('0')) < quantity:
            raise InsufficientHoldings(f"Insufficient holdings for {symbol}")
        price = get_share_price(symbol)
        total_proceeds = price * quantity
        self.cash_balance += total_proceeds
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.transactions.append(TransactionRecord({
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': TransactionType.SELL,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': total_proceeds,
            'details': f"Sold {quantity} shares of {symbol} at ${price} per share"
        }))

    def get_transaction_history(self) -> List[TransactionRecord]:
        return self.transactions

    def get_holdings_report(self) -> Dict[str, HoldingDetail]:
        report = {}
        for symbol, quantity in self.holdings.items():
            price = get_share_price(symbol)
            report[symbol] = HoldingDetail({
                'symbol': symbol,
                'quantity': quantity,
                'current_price': price,
                'market_value': price * quantity
            })
        return report

    def get_portfolio_summary(self) -> PortfolioSummary:
        report = self.get_holdings_report()
        total_market_value = sum(v['market_value'] for v in report.values())
        total_portfolio_value = self.cash_balance + total_market_value
        profit_loss = total_portfolio_value - self.deposits_baseline
        return PortfolioSummary({
            'cash_balance': self.cash_balance,
            'total_market_value': total_market_value,
            'total_portfolio_value': total_portfolio_value,
            'total_deposits_baseline': self.deposits_baseline,
            'profit_loss': profit_loss,
        })
