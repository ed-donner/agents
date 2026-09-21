import unittest
from accounts import get_share_price, Account

class TestGetSharePrice(unittest.TestCase):
    def test_valid_symbols(self):
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('TSLA'), 800.0)
        self.assertEqual(get_share_price('GOOGL'), 2500.0)
    
    def test_invalid_symbol(self):
        self.assertEqual(get_share_price('INVALID'), 0.0)

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account('test_user', 10000.0)
    
    def test_initialization(self):
        self.assertEqual(self.account.user_id, 'test_user')
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.initial_deposit, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]['type'], 'deposit')
    
    def test_deposit_funds(self):
        self.account.deposit_funds(500.0)
        self.assertEqual(self.account.balance, 10500.0)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]['type'], 'deposit')
    
    def test_withdraw_funds_success(self):
        result = self.account.withdraw_funds(1000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 9000.0)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]['type'], 'withdrawal')
    
    def test_withdraw_funds_failure(self):
        result = self.account.withdraw_funds(20000.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(len(self.account.transactions), 1)
    
    def test_buy_shares_success(self):
        result = self.account.buy_shares('AAPL', 10)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 10))
        self.assertEqual(self.account.holdings, {'AAPL': 10})
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]['type'], 'buy')
    
    def test_buy_shares_failure(self):
        result = self.account.buy_shares('AAPL', 1000)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
    
    def test_sell_shares_success(self):
        self.account.buy_shares('AAPL', 10)
        result = self.account.sell_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 10) + (150.0 * 5))
        self.assertEqual(self.account.holdings, {'AAPL': 5})
        self.assertEqual(len(self.account.transactions), 3)
    
    def test_sell_shares_failure(self):
        result = self.account.sell_shares('AAPL', 5)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
    
    def test_calculate_portfolio_value(self):
        self.account.buy_shares('AAPL', 10)
        self.account.buy_shares('TSLA', 5)
        expected_value = (10000.0 - (150.0 * 10) - (800.0 * 5)) + (150.0 * 10) + (800.0 * 5)
        self.assertEqual(self.account.calculate_portfolio_value(), expected_value)
    
    def test_calculate_profit_or_loss(self):
        self.account.buy_shares('AAPL', 10)
        portfolio_value = self.account.calculate_portfolio_value()
        expected_profit_loss = portfolio_value - 10000.0
        self.assertEqual(self.account.calculate_profit_or_loss(), expected_profit_loss)
    
    def test_get_holdings(self):
        self.account.buy_shares('AAPL', 10)
        holdings = self.account.get_holdings()
        self.assertEqual(holdings, {'AAPL': 10})
        # Test that it's a copy
        holdings['AAPL'] = 5
        self.assertEqual(self.account.holdings, {'AAPL': 10})
    
    def test_get_transactions(self):
        self.account.deposit_funds(500.0)
        transactions = self.account.get_transactions()
        self.assertEqual(len(transactions), 2)
        # Test that it's a copy
        transactions.append({'test': 'data'})
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_get_report(self):
        report = self.account.get_report()
        self.assertEqual(report['user_id'], 'test_user')
        self.assertEqual(report['balance'], 10000.0)
        self.assertEqual(report['holdings'], {})
        self.assertEqual(report['portfolio_value'], 10000.0)
        self.assertEqual(report['profit_or_loss'], 0.0)

if __name__ == '__main__':
    unittest.main()