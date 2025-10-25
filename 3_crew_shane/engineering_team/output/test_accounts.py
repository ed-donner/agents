import unittest
from unittest.mock import patch

# Import from accounts module
from accounts import get_share_price, Transaction, Account


class TestGetSharePrice(unittest.TestCase):
    def test_known_symbols(self):
        # Test that known symbols return expected values
        self.assertEqual(get_share_price('AAPL'), 150.00)
        self.assertEqual(get_share_price('TSLA'), 650.00)
        self.assertEqual(get_share_price('GOOGL'), 2800.00)
    
    def test_unknown_symbol(self):
        # Test that unknown symbols return 0.0
        self.assertEqual(get_share_price('UNKNOWN'), 0.0)


class TestTransaction(unittest.TestCase):
    def test_buy_transaction_init(self):
        # Test creating a buy transaction
        tx = Transaction('buy', 'AAPL', 10, 150.00)
        self.assertEqual(tx.action, 'buy')
        self.assertEqual(tx.symbol, 'AAPL')
        self.assertEqual(tx.quantity, 10)
        self.assertEqual(tx.price, 150.00)
        self.assertEqual(tx.amount, 0.0)
    
    def test_deposit_transaction_init(self):
        # Test creating a deposit transaction
        tx = Transaction('deposit', amount=1000.00)
        self.assertEqual(tx.action, 'deposit')
        self.assertIsNone(tx.symbol)
        self.assertEqual(tx.quantity, 0)
        self.assertEqual(tx.price, 0.0)
        self.assertEqual(tx.amount, 1000.00)
    
    def test_transaction_str_buy_sell(self):
        # Test string representation for buy/sell transactions
        tx = Transaction('buy', 'AAPL', 10, 150.00)
        self.assertEqual(str(tx), "Buy 10 AAPL @ $150.00")
        
        tx = Transaction('sell', 'TSLA', 5, 650.00)
        self.assertEqual(str(tx), "Sell 5 TSLA @ $650.00")
    
    def test_transaction_str_deposit_withdraw(self):
        # Test string representation for deposit/withdraw transactions
        tx = Transaction('deposit', amount=1000.00)
        self.assertEqual(str(tx), "Deposit $1000.00")
        
        tx = Transaction('withdraw', amount=500.00)
        self.assertEqual(str(tx), "Withdraw $500.00")


class TestAccount(unittest.TestCase):
    def test_init_with_valid_deposit(self):
        # Test creating an account with a valid initial deposit
        account = Account(1000.0)
        self.assertEqual(account.balance, 1000.0)
        self.assertEqual(account.holdings, {})
        self.assertEqual(len(account.transactions), 1)
        self.assertEqual(account.transactions[0].action, 'deposit')
        self.assertEqual(account.transactions[0].amount, 1000.0)
    
    def test_init_with_invalid_deposit(self):
        # Test creating an account with an invalid initial deposit
        with self.assertRaises(ValueError):
            Account(0)
        with self.assertRaises(ValueError):
            Account(-100.0)
    
    def test_deposit(self):
        # Test deposit method
        account = Account(1000.0)
        account.deposit(500.0)
        self.assertEqual(account.balance, 1500.0)
        self.assertEqual(len(account.transactions), 2)
        self.assertEqual(account.transactions[1].action, 'deposit')
        self.assertEqual(account.transactions[1].amount, 500.0)
    
    def test_deposit_invalid_amount(self):
        # Test deposit with invalid amount
        account = Account(1000.0)
        with self.assertRaises(ValueError):
            account.deposit(0)
        with self.assertRaises(ValueError):
            account.deposit(-100.0)
    
    def test_withdraw(self):
        # Test withdraw method
        account = Account(1000.0)
        account.withdraw(300.0)
        self.assertEqual(account.balance, 700.0)
        self.assertEqual(len(account.transactions), 2)
        self.assertEqual(account.transactions[1].action, 'withdraw')
        self.assertEqual(account.transactions[1].amount, 300.0)
    
    def test_withdraw_invalid_amount(self):
        # Test withdraw with invalid amount
        account = Account(1000.0)
        with self.assertRaises(ValueError):
            account.withdraw(0)
        with self.assertRaises(ValueError):
            account.withdraw(-100.0)
        with self.assertRaises(ValueError):
            account.withdraw(1500.0)  # More than balance
    
    def test_buy_shares(self):
        # Test buying shares
        account = Account(2000.0)
        account.buy_shares('AAPL', 10)  # 10 * $150 = $1500
        self.assertEqual(account.balance, 500.0)
        self.assertEqual(account.holdings, {'AAPL': 10})
        self.assertEqual(len(account.transactions), 2)
        self.assertEqual(account.transactions[1].action, 'buy')
        self.assertEqual(account.transactions[1].symbol, 'AAPL')
        self.assertEqual(account.transactions[1].quantity, 10)
        self.assertEqual(account.transactions[1].price, 150.00)
    
    def test_buy_shares_invalid(self):
        # Test buying with invalid parameters
        account = Account(1000.0)
        with self.assertRaises(ValueError):
            account.buy_shares('AAPL', 0)  # Invalid quantity
        with self.assertRaises(ValueError):
            account.buy_shares('AAPL', -5)  # Invalid quantity
        with self.assertRaises(ValueError):
            account.buy_shares('UNKNOWN', 5)  # Unknown symbol
        with self.assertRaises(ValueError):
            account.buy_shares('AAPL', 10)  # Not enough funds (10*150 > 1000)
    
    def test_buy_shares_multiple_symbols(self):
        # Test buying multiple different shares
        account = Account(5000.0)
        account.buy_shares('AAPL', 10)  # 10 * $150 = $1500
        account.buy_shares('TSLA', 5)   # 5 * $650 = $3250
        self.assertEqual(account.balance, 250.0)
        self.assertEqual(account.holdings, {'AAPL': 10, 'TSLA': 5})
    
    def test_buy_shares_price_change(self):
        # Test buying shares when price changes
        account = Account(2000.0)
        with patch('accounts.get_share_price', return_value=200.0):
            account.buy_shares('AAPL', 5)  # 5 * $200 = $1000
            self.assertEqual(account.balance, 1000.0)
            self.assertEqual(account.holdings, {'AAPL': 5})
    
    def test_sell_shares(self):
        # Test selling shares
        account = Account(2000.0)
        account.buy_shares('AAPL', 10)  # 10 * $150 = $1500
        account.sell_shares('AAPL', 5)  # 5 * $150 = $750
        self.assertEqual(account.balance, 1250.0)
        self.assertEqual(account.holdings, {'AAPL': 5})
        self.assertEqual(account.transactions[-1].action, 'sell')
        self.assertEqual(account.transactions[-1].symbol, 'AAPL')
        self.assertEqual(account.transactions[-1].quantity, 5)
    
    def test_sell_shares_all(self):
        # Test selling all shares of a symbol
        account = Account(2000.0)
        account.buy_shares('AAPL', 10)  # 10 * $150 = $1500
        account.sell_shares('AAPL', 10)  # 10 * $150 = $1500
        self.assertEqual(account.balance, 2000.0)
        self.assertEqual(account.holdings, {})
    
    def test_sell_shares_invalid(self):
        # Test selling with invalid parameters
        account = Account(2000.0)
        account.buy_shares('AAPL', 10)
        with self.assertRaises(ValueError):
            account.sell_shares('AAPL', 0)  # Invalid quantity
        with self.assertRaises(ValueError):
            account.sell_shares('AAPL', -5)  # Invalid quantity
        with self.assertRaises(ValueError):
            account.sell_shares('AAPL', 15)  # Not enough shares
        with self.assertRaises(ValueError):
            account.sell_shares('TSLA', 5)  # Don't own the shares
    
    def test_portfolio_value_empty(self):
        # Test portfolio value with empty holdings
        account = Account(1000.0)
        self.assertEqual(account.portfolio_value(), 1000.0)  # Just the balance
    
    def test_portfolio_value(self):
        # Test portfolio value calculation
        account = Account(1000.0)
        account.buy_shares('AAPL', 5)  # 5 * $150 = $750, balance = $250
        # Portfolio value: $250 (balance) + 5*$150 = $1000
        self.assertEqual(account.portfolio_value(), 1000.0)
        
        # Test with changing stock prices
        with patch('accounts.get_share_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 200.0}.get(symbol, 0.0)
            # With new price: 5 * $200 = $1000, balance still $250
            # Portfolio value should be $1250
            self.assertEqual(account.portfolio_value(), 1250.0)
    
    def test_total_deposits(self):
        # Test total deposits calculation
        account = Account(1000.0)
        account.deposit(500.0)
        account.withdraw(200.0)
        account.deposit(300.0)
        # Initial 1000 + 500 - 200 + 300 = 1600
        self.assertEqual(account.total_deposits(), 1600.0)
    
    def test_profit_loss(self):
        # Test profit/loss calculation
        account = Account(1000.0)
        # No activity yet, so profit/loss should be 0
        self.assertEqual(account.profit_loss(), 0.0)
        
        # Buy shares and then share price increases
        account.buy_shares('AAPL', 5)  # 5 * $150 = $750, balance = $250
        with patch('accounts.get_share_price') as mock_price:
            mock_price.return_value = 200.0
            # With new price: 5 * $200 = $1000, balance still $250
            # Portfolio value is $1250, deposits are $1000
            # Profit is $250
            self.assertEqual(account.profit_loss(), 250.0)
    
    def test_report_holdings(self):
        # Test report_holdings method
        account = Account(2000.0)
        account.buy_shares('AAPL', 10)
        account.buy_shares('TSLA', 1)
        holdings = account.report_holdings()
        self.assertEqual(holdings, {'AAPL': 10, 'TSLA': 1})
        # Ensure it's a copy, not the actual dictionary
        holdings['TEST'] = 5
        self.assertNotIn('TEST', account.holdings)
    
    def test_report_profit_loss(self):
        # Test report_profit_loss method
        account = Account(1000.0)
        with patch.object(Account, 'profit_loss', return_value=250.0):
            self.assertEqual(account.report_profit_loss(), 250.0)
    
    def test_list_transactions(self):
        # Test list_transactions method
        account = Account(1000.0)
        account.deposit(500.0)
        account.withdraw(200.0)
        transactions = account.list_transactions()
        self.assertEqual(len(transactions), 3)
        # Ensure it's a copy, not the actual list
        original_len = len(account.transactions)
        transactions.append('dummy')
        self.assertEqual(len(account.transactions), original_len)


if __name__ == '__main__':
    unittest.main()