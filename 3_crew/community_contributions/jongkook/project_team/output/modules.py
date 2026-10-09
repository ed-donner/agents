"""
Trading Simulation Platform Modules

Modules included:
1. UserAccount - Handles user account creation, deposits, and withdrawals.
2. Transaction - Manages buying and selling transactions.
3. Portfolio - Manages holdings and portfolio valuation.
4. Market - Fetches current share prices.

Each module is self-contained and includes unit tests.
"""

import unittest

class Market:
    """Market Module: Fetch current share prices."""

    # Mock prices for demonstration. In real application, fetch from API.
    _prices = {
        'AAPL': 150.0,
        'GOOG': 2800.0,
        'TSLA': 700.0,
        'MSFT': 300.0,
        'AMZN': 3300.0
    }

    @staticmethod
    def get_share_price(symbol):
        price = Market._prices.get(symbol)
        if price is None:
            raise ValueError(f"Price for symbol '{symbol}' not found.")
        return price


class UserAccount:
    """UserAccount Module: Manages user accounts and balances."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.balance = 0.0

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount


class Portfolio:
    """Portfolio Module: Manages holdings and calculates portfolio value."""

    def __init__(self):
        # holdings = {symbol: quantity}
        self.holdings = {}

    def add_shares(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to add must be positive.")
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity

    def remove_shares(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to remove must be positive.")
        current_qty = self.holdings.get(symbol, 0)
        if quantity > current_qty:
            raise ValueError(f"Not enough shares to sell: {quantity} requested, {current_qty} available.")
        new_qty = current_qty - quantity
        if new_qty == 0:
            del self.holdings[symbol]
        else:
            self.holdings[symbol] = new_qty

    def calculate_total_value(self):
        total = 0.0
        for symbol, qty in self.holdings.items():
            price = Market.get_share_price(symbol)
            total += price * qty
        return total

    def report_holdings(self):
        return dict(self.holdings)  # return a copy

    def assess_profit_loss(self, initial_deposit):
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")
        current_value = self.calculate_total_value()
        return current_value - initial_deposit


class Transaction:
    """Transaction Module: Manages buying and selling shares with checking."""

    def __init__(self, user_account, portfolio):
        self.user_account = user_account
        self.portfolio = portfolio
        self.transactions = []  # list of dicts recording each transaction

    def buy_shares(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to buy must be positive.")
        price_per_share = Market.get_share_price(symbol)
        total_cost = price_per_share * quantity
        if total_cost > self.user_account.balance:
            raise ValueError("Insufficient funds to buy shares.")
        # Deduct funds
        self.user_account.withdraw(total_cost)
        # Add shares
        self.portfolio.add_shares(symbol, quantity)
        # Record transaction
        self.transactions.append({
            'type': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'total_cost': total_cost
        })

    def sell_shares(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to sell must be positive.")
        # Check if user owns enough shares
        current_qty = self.portfolio.holdings.get(symbol, 0)
        if quantity > current_qty:
            raise ValueError("Insufficient shares to sell.")
        price_per_share = Market.get_share_price(symbol)
        total_gain = price_per_share * quantity
        # Remove shares
        self.portfolio.remove_shares(symbol, quantity)
        # Add funds
        self.user_account.deposit(total_gain)
        # Record transaction
        self.transactions.append({
            'type': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'total_gain': total_gain
        })


# Unit tests for all modules
class TestTradingSimulation(unittest.TestCase):

    def setUp(self):
        self.user = UserAccount("user1")
        self.portfolio = Portfolio()
        self.transaction = Transaction(self.user, self.portfolio)

    # UserAccount tests
    def test_deposit_and_withdraw(self):
        self.user.deposit(1000)
        self.assertEqual(self.user.balance, 1000)
        self.user.withdraw(200)
        self.assertEqual(self.user.balance, 800)

    def test_withdraw_insufficient_funds(self):
        self.user.deposit(100)
        with self.assertRaises(ValueError):
            self.user.withdraw(200)

    def test_deposit_negative(self):
        with self.assertRaises(ValueError):
            self.user.deposit(-50)

    def test_withdraw_negative(self):
        with self.assertRaises(ValueError):
            self.user.withdraw(-50)

    # Market tests
    def test_get_share_price(self):
        price = Market.get_share_price('AAPL')
        self.assertEqual(price, 150.0)
        with self.assertRaises(ValueError):
            Market.get_share_price('UNKNOWN')

    # Portfolio tests
    def test_add_and_remove_shares(self):
        self.portfolio.add_shares('AAPL', 10)
        self.assertEqual(self.portfolio.holdings['AAPL'], 10)
        self.portfolio.remove_shares('AAPL', 5)
        self.assertEqual(self.portfolio.holdings['AAPL'], 5)

    def test_remove_shares_too_many(self):
        self.portfolio.add_shares('TSLA', 5)
        with self.assertRaises(ValueError):
            self.portfolio.remove_shares('TSLA', 10)

    def test_calculate_total_value(self):
        self.portfolio.add_shares('AAPL', 2)  # 2*150 = 300
        self.portfolio.add_shares('GOOG', 1)  # 1*2800 = 2800
        total_value = self.portfolio.calculate_total_value()
        self.assertEqual(total_value, 3100.0)

    def test_assess_profit_loss(self):
        self.portfolio.add_shares('AAPL', 5)  # 5*150=750
        profit_loss = self.portfolio.assess_profit_loss(700)
        self.assertEqual(profit_loss, 50)

    def test_assess_profit_loss_negative_deposit(self):
        with self.assertRaises(ValueError):
            self.portfolio.assess_profit_loss(-100)

    # Transaction tests
    def test_buy_shares_success(self):
        self.user.deposit(1000)
        self.transaction.buy_shares('AAPL', 5)  # 5*150=750
        self.assertEqual(self.user.balance, 250)
        self.assertEqual(self.portfolio.holdings['AAPL'], 5)
        self.assertEqual(len(self.transaction.transactions), 1)

    def test_buy_shares_insufficient_funds(self):
        self.user.deposit(100)
        with self.assertRaises(ValueError):
            self.transaction.buy_shares('GOOG', 1)  # 2800 > 100

    def test_sell_shares_success(self):
        self.portfolio.add_shares('TSLA', 10)
        self.transaction.sell_shares('TSLA', 5)  # user not credited yet
        self.assertEqual(self.portfolio.holdings['TSLA'], 5)
        self.assertEqual(self.user.balance, 3500)  # 5*700
        self.assertEqual(len(self.transaction.transactions), 1)

    def test_sell_shares_insufficient_shares(self):
        self.portfolio.add_shares('MSFT', 2)
        with self.assertRaises(ValueError):
            self.transaction.sell_shares('MSFT', 5)


if __name__ == '__main__':
    unittest.main()