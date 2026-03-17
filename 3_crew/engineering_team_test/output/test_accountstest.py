import unittest
from accountstest import Accounttest, get_share_price

class TestAccounttest(unittest.TestCase):

    def setUp(self):
        self.account = Accounttest('12345', 1000.0)

    def test_initialization(self):
        self.assertEqual(self.account.account_id, '12345')
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(self.account.balance, 1000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])

    def test_deposit_funds(self):
        self.account.deposit_funds(500.0)
        self.assertEqual(self.account.balance, 1500.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0], {'type': 'deposit', 'amount': 500.0})

    def test_withdraw_funds(self):
        result = self.account.withdraw_funds(300.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 700.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0], {'type': 'withdraw', 'amount': 300.0})

        result = self.account.withdraw_funds(800.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 700.0)  # Balance should not change
        self.assertEqual(len(self.account.transactions), 1)  # No new transaction

    def test_buy_shares(self):
        result = self.account.buy_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings['AAPL'], 5)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0], {'type': 'buy', 'symbol': 'AAPL', 'quantity': 5})

        result = self.account.buy_shares('AAPL', 100)
        self.assertFalse(result)  # Insufficient funds
        self.assertEqual(self.account.holdings['AAPL'], 5)
        self.assertEqual(len(self.account.transactions), 1)  # No new transaction

    def test_sell_shares(self):
        self.account.buy_shares('AAPL', 5)
        result = self.account.sell_shares('AAPL', 3)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings['AAPL'], 2)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1], {'type': 'sell', 'symbol': 'AAPL', 'quantity': 3})

        result = self.account.sell_shares('AAPL', 4)
        self.assertFalse(result)  # Not enough shares
        self.assertEqual(self.account.holdings['AAPL'], 2)
        self.assertEqual(len(self.account.transactions), 2)  # No new transaction

    def test_get_total_portfolio_value(self):
        self.assertEqual(self.account.get_total_portfolio_value(), 1000.0)
        self.account.buy_shares('AAPL', 5)
        expected_value = 1000.0 - 750.0 + 750.0  # initial - cost of shares + value of shares
        self.assertEqual(self.account.get_total_portfolio_value(), expected_value)

    def test_get_profit_loss(self):
        self.assertEqual(self.account.get_profit_loss(), 0.0)
        self.account.buy_shares('AAPL', 5)
        self.assertEqual(self.account.get_profit_loss(), 0.0)
        self.account.sell_shares('AAPL', 5)
        self.assertEqual(self.account.get_profit_loss(), 0.0)

    def test_get_holdings(self):
        self.assertEqual(self.account.get_holdings(), {})
        self.account.buy_shares('AAPL', 5)
        self.assertEqual(self.account.get_holdings(), {'AAPL': 5})

    def test_get_transactions(self):
        self.assertEqual(self.account.get_transactions(), [])
        self.account.deposit_funds(500.0)
        self.assertEqual(len(self.account.get_transactions()), 1)
        self.account.withdraw_funds(200.0)
        self.assertEqual(len(self.account.get_transactions()), 2)

    def test_get_share_price(self):
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('TSLA'), 650.0)
        self.assertEqual(get_share_price('GOOGL'), 2800.0)
        self.assertEqual(get_share_price('UNKNOWN'), 0.0) 

if __name__ == '__main__':
    unittest.main()