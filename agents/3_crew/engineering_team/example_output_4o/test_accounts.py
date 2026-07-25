import unittest
from unittest.mock import Mock, patch

class TestGetSharePrice(unittest.TestCase):
    """Tests for the get_share_price function"""
    
    def test_known_symbols(self):
        """Test that known symbols return the expected prices"""
        from accounts import get_share_price
        
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('TSLA'), 800.0)
        self.assertEqual(get_share_price('GOOGL'), 2500.0)
        
    def test_unknown_symbol(self):
        """Test that unknown symbols return 0.0"""
        from accounts import get_share_price
        
        self.assertEqual(get_share_price('UNKNOWN'), 0.0)


class TestAccount(unittest.TestCase):
    """Tests for the Account class"""
    
    def setUp(self):
        """Set up a test account before each test"""
        from accounts import Account
        self.account = Account('test123')
        
    def test_init(self):
        """Test account initialization"""
        self.assertEqual(self.account.account_id, 'test123')
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])
        self.assertEqual(self.account.initial_deposit, 0.0)
    
    def test_deposit_valid(self):
        """Test valid deposit"""
        result = self.account.deposit(1000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 1000.0)
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]['type'], 'deposit')
        self.assertEqual(self.account.transactions[0]['amount'], 1000.0)
        
        # Add another deposit
        result = self.account.deposit(500.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 1500.0)
        # Initial deposit should still be the first deposit
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_deposit_invalid(self):
        """Test invalid deposits (zero or negative amounts)"""
        result = self.account.deposit(0.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(len(self.account.transactions), 0)
        
        result = self.account.deposit(-100.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(len(self.account.transactions), 0)

    def test_withdraw_valid(self):
        """Test valid withdrawal"""
        self.account.deposit(1000.0)
        result = self.account.withdraw(500.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 500.0)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]['type'], 'withdraw')
        self.assertEqual(self.account.transactions[1]['amount'], 500.0)
    
    def test_withdraw_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        self.account.deposit(100.0)
        result = self.account.withdraw(200.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(len(self.account.transactions), 1)  # Only the deposit transaction
    
    def test_withdraw_negative_amount(self):
        """Test withdrawal with negative amount"""
        self.account.deposit(100.0)
        result = self.account.withdraw(-50.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(len(self.account.transactions), 1)  # Only the deposit transaction

    def test_buy_shares_valid(self):
        """Test buying shares with sufficient funds"""
        from accounts import get_share_price
        
        self.account.deposit(1000.0)
        result = self.account.buy_shares('AAPL', 5, get_share_price)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 250.0)  # 1000 - (5 * 150)
        self.assertEqual(self.account.holdings['AAPL'], 5)
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1]['type'], 'buy')
        self.assertEqual(self.account.transactions[1]['symbol'], 'AAPL')
        self.assertEqual(self.account.transactions[1]['quantity'], 5)
        
        # Buy more of the same stock
        result = self.account.buy_shares('AAPL', 1, get_share_price)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 100.0)  # 250 - (1 * 150)
        self.assertEqual(self.account.holdings['AAPL'], 6)

    def test_buy_shares_insufficient_funds(self):
        """Test buying shares with insufficient funds"""
        from accounts import get_share_price
        
        self.account.deposit(100.0)
        result = self.account.buy_shares('AAPL', 5, get_share_price)  # Costs 750.0
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)  # Only the deposit transaction

    def test_buy_shares_invalid_quantity(self):
        """Test buying shares with invalid quantity"""
        from accounts import get_share_price
        
        self.account.deposit(1000.0)
        result = self.account.buy_shares('AAPL', 0, get_share_price)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 1000.0)
        self.assertEqual(self.account.holdings, {})
        
        result = self.account.buy_shares('AAPL', -5, get_share_price)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 1000.0)
        self.assertEqual(self.account.holdings, {})

    def test_sell_shares_valid(self):
        """Test selling shares that the user owns"""
        from accounts import get_share_price
        
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 5, get_share_price)
        result = self.account.sell_shares('AAPL', 2, get_share_price)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 550.0)  # 250 + (2 * 150)
        self.assertEqual(self.account.holdings['AAPL'], 3)
        self.assertEqual(len(self.account.transactions), 3)
        self.assertEqual(self.account.transactions[2]['type'], 'sell')
        
        # Sell remaining shares
        result = self.account.sell_shares('AAPL', 3, get_share_price)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 1000.0)  # 550 + (3 * 150)
        self.assertNotIn('AAPL', self.account.holdings)  # All shares sold

    def test_sell_shares_insufficient_shares(self):
        """Test selling more shares than the user owns"""
        from accounts import get_share_price
        
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 5, get_share_price)
        result = self.account.sell_shares('AAPL', 10, get_share_price)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 250.0)  # Unchanged
        self.assertEqual(self.account.holdings['AAPL'], 5)  # Unchanged

    def test_sell_shares_invalid_quantity(self):
        """Test selling an invalid quantity of shares"""
        from accounts import get_share_price
        
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 5, get_share_price)
        result = self.account.sell_shares('AAPL', 0, get_share_price)
        self.assertFalse(result)
        self.assertEqual(self.account.holdings['AAPL'], 5)  # Unchanged
        
        result = self.account.sell_shares('AAPL', -2, get_share_price)
        self.assertFalse(result)
        self.assertEqual(self.account.holdings['AAPL'], 5)  # Unchanged

    def test_get_portfolio_value(self):
        """Test getting the portfolio value"""
        from accounts import get_share_price, Account
        
        # Create a real account with holdings
        account = Account('test')
        account.holdings = {'AAPL': 5, 'TSLA': 2}
        
        # Calculate expected value: (5 * 150) + (2 * 800) = 750 + 1600 = 2350
        expected_value = 2350.0
        actual_value = account.get_portfolio_value(get_share_price)
        
        self.assertEqual(actual_value, expected_value)

    def test_get_profit_or_loss(self):
        """Test calculating profit or loss"""
        from accounts import Account, get_share_price
        
        account = Account('test')
        account.deposit(1000.0)  # Initial deposit
        
        # No stocks, no profit/loss yet
        self.assertEqual(account.get_profit_or_loss(get_share_price), 0.0)
        
        # Buy some stocks
        account.buy_shares('AAPL', 5, get_share_price)  # Costs 750
        
        # Current state: 250 balance + (5 * 150) in stocks = 1000, so profit/loss is 0
        self.assertEqual(account.get_profit_or_loss(get_share_price), 0.0)
        
        # Simulate price change by using a custom price function
        def higher_prices(symbol):
            prices = {
                'AAPL': 200.0,  # Increased from 150
                'TSLA': 800.0,
                'GOOGL': 2500.0
            }
            return prices.get(symbol, 0.0)
        
        # With higher prices: 250 balance + (5 * 200) in stocks = 1250, so profit is 250
        self.assertEqual(account.get_profit_or_loss(higher_prices), 250.0)

    def test_get_holdings(self):
        """Test getting a copy of the user's holdings"""
        from accounts import Account, get_share_price
        
        account = Account('test')
        account.deposit(1000.0)
        account.buy_shares('AAPL', 5, get_share_price)
        
        holdings = account.get_holdings()
        self.assertEqual(holdings, {'AAPL': 5})
        
        # Verify it's a copy by modifying the returned dict
        holdings['AAPL'] = 10
        self.assertEqual(account.holdings['AAPL'], 5)  # Original unchanged

    def test_get_transactions(self):
        """Test getting a copy of the user's transactions"""
        from accounts import Account, get_share_price
        
        account = Account('test')
        account.deposit(1000.0)
        account.buy_shares('AAPL', 5, get_share_price)
        
        transactions = account.get_transactions()
        self.assertEqual(len(transactions), 2)
        
        # Verify it's a copy by modifying the returned list
        transactions.append({'fake': 'transaction'})
        self.assertEqual(len(account.transactions), 2)  # Original unchanged

    def test_can_withdraw(self):
        """Test the can_withdraw check method"""
        from accounts import Account
        
        account = Account('test')
        account.deposit(100.0)
        
        self.assertTrue(account.can_withdraw(50.0))
        self.assertTrue(account.can_withdraw(100.0))
        self.assertFalse(account.can_withdraw(150.0))
        self.assertFalse(account.can_withdraw(0.0))
        self.assertFalse(account.can_withdraw(-50.0))

    def test_can_buy_shares(self):
        """Test the can_buy_shares check method"""
        from accounts import Account, get_share_price
        
        account = Account('test')
        account.deposit(1000.0)
        
        # Can buy shares with sufficient funds
        self.assertTrue(account.can_buy_shares('AAPL', 6, get_share_price))  # 6 * 150 = 900
        self.assertTrue(account.can_buy_shares('AAPL', 6.5, get_share_price))  # 6.5 * 150 = 975
        
        # Cannot buy shares with insufficient funds
        self.assertFalse(account.can_buy_shares('AAPL', 7, get_share_price))  # 7 * 150 = 1050
        
        # Cannot buy invalid quantities
        self.assertFalse(account.can_buy_shares('AAPL', 0, get_share_price))
        self.assertFalse(account.can_buy_shares('AAPL', -5, get_share_price))
        
        # Cannot buy shares with 0 price
        self.assertFalse(account.can_buy_shares('UNKNOWN', 5, get_share_price))

    def test_can_sell_shares(self):
        """Test the can_sell_shares check method"""
        from accounts import Account, get_share_price
        
        account = Account('test')
        account.deposit(1000.0)
        account.buy_shares('AAPL', 5, get_share_price)
        
        # Can sell shares the user owns
        self.assertTrue(account.can_sell_shares('AAPL', 3))
        self.assertTrue(account.can_sell_shares('AAPL', 5))
        
        # Cannot sell more shares than the user owns
        self.assertFalse(account.can_sell_shares('AAPL', 6))
        
        # Cannot sell shares the user doesn't own
        self.assertFalse(account.can_sell_shares('TSLA', 1))
        
        # Cannot sell invalid quantities
        self.assertFalse(account.can_sell_shares('AAPL', 0))
        self.assertFalse(account.can_sell_shares('AAPL', -1))


if __name__ == '__main__':
    unittest.main()