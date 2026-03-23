import unittest
from datetime import datetime
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account("test_user")

    def test_initial_state(self):
        self.assertEqual(self.account.user_id, "test_user")
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])
        self.assertEqual(self.account.initial_deposit, 0.0)

    def test_get_share_price(self):
        self.assertEqual(get_share_price("AAPL"), 150.0)
        self.assertEqual(get_share_price("INVALID"), 0.0)

    def test_deposit(self):
        self.account.deposit(1000.0)
        self.assertEqual(self.account.balance, 1000.0)
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]["type"], "deposit")

    def test_deposit_negative_amount(self):
        with self.assertRaises(ValueError):
            self.account.deposit(-100.0)

    def test_withdraw(self):
        self.account.deposit(1000.0)
        self.account.withdraw(500.0)
        self.assertEqual(self.account.balance, 500.0)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]["type"], "withdrawal")

    def test_withdraw_insufficient_funds(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(100.0)

    def test_withdraw_negative_amount(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(-100.0)

    def test_buy_shares(self):
        self.account.deposit(2000.0)
        self.account.buy_shares("AAPL", 10)
        self.assertEqual(self.account.holdings["AAPL"], 10)
        self.assertEqual(self.account.balance, 500.0)  # 2000 - (150 * 10)

    def test_buy_shares_insufficient_funds(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", 10)

    def test_buy_shares_invalid_symbol(self):
        self.account.deposit(2000.0)
        with self.assertRaises(ValueError):
            self.account.buy_shares("INVALID", 10)

    def test_sell_shares(self):
        self.account.deposit(2000.0)
        self.account.buy_shares("AAPL", 10)
        self.account.sell_shares("AAPL", 5)
        self.assertEqual(self.account.holdings["AAPL"], 5)
        self.assertEqual(self.account.balance, 1250.0)  # 500 + (150 * 5)

    def test_sell_shares_insufficient_shares(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 1)

    def test_calculate_portfolio_value(self):
        self.account.deposit(2000.0)
        self.account.buy_shares("AAPL", 10)
        portfolio_value = self.account.calculate_portfolio_value()
        expected_value = 500.0 + (150.0 * 10)  # balance + (share_price * quantity)
        self.assertEqual(portfolio_value, expected_value)

    def test_calculate_profit_loss(self):
        self.account.deposit(2000.0)
        self.account.buy_shares("AAPL", 10)
        profit_loss = self.account.calculate_profit_loss()
        expected_pl = (500.0 + (150.0 * 10)) - 2000.0  # portfolio_value - initial_deposit
        self.assertEqual(profit_loss, expected_pl)

    def test_get_holdings(self):
        self.account.deposit(2000.0)
        self.account.buy_shares("AAPL", 10)
        holdings = self.account.get_holdings()
        self.assertEqual(holdings["AAPL"], 10)
        # Verify it's a copy
        holdings["AAPL"] = 0
        self.assertEqual(self.account.holdings["AAPL"], 10)

    def test_get_transaction_history(self):
        self.account.deposit(1000.0)
        self.account.withdraw(500.0)
        transactions = self.account.get_transaction_history()
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]["type"], "deposit")
        self.assertEqual(transactions[1]["type"], "withdrawal")

if __name__ == "__main__":
    unittest.main()