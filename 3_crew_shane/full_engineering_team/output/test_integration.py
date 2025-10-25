#!/usr/bin/env python3
import unittest
import logging

from backend.user_management import user_manager
from backend.financial import financial_manager
from backend.trading import trading_manager
from backend.portfolio import portfolio_manager
from backend.price_service import price_service
from backend.transaction_history import transaction_history

class TestTradingPlatformIntegration(unittest.TestCase):
    def setUp(self):
        # Disable logging during tests
        logging.disable(logging.CRITICAL)
        
        # Create a test user
        self.username = f"test_user_{hash(self.__class__.__name__)}"
        self.password = "password123"
        user = user_manager.create_user(self.username, self.password)
        self.assertIsNotNone(user)
        self.user_id = user['id']
        
        # Add initial funds
        success = financial_manager.deposit(self.user_id, 10000.0, "Test deposit")
        self.assertTrue(success)
    
    def tearDown(self):
        # Re-enable logging
        logging.disable(logging.NOTSET)
        
        # In a real test, we would clean up the test data
        # For simplicity, we'll leave the test user in the database
    
    def test_user_authentication(self):
        """Test user authentication."""
        # Test successful authentication
        user = user_manager.authenticate_user(self.username, self.password)
        self.assertIsNotNone(user)
        self.assertEqual(user['id'], self.user_id)
        
        # Test failed authentication
        user = user_manager.authenticate_user(self.username, "wrong_password")
        self.assertIsNone(user)
    
    def test_financial_operations(self):
        """Test financial operations."""
        # Test get balance
        balance = financial_manager.get_balance(self.user_id)
        self.assertEqual(balance, 10000.0)
        
        # Test deposit
        success = financial_manager.deposit(self.user_id, 1000.0)
        self.assertTrue(success)
        
        balance = financial_manager.get_balance(self.user_id)
        self.assertEqual(balance, 11000.0)
        
        # Test withdrawal
        success = financial_manager.withdraw(self.user_id, 500.0)
        self.assertTrue(success)
        
        balance = financial_manager.get_balance(self.user_id)
        self.assertEqual(balance, 10500.0)
        
        # Test invalid withdrawal (insufficient funds)
        success = financial_manager.withdraw(self.user_id, 20000.0)
        self.assertFalse(success)
        
        # Test transaction history
        transactions = transaction_history.get_transaction_history(self.user_id)
        self.assertEqual(len(transactions), 3)  # Initial deposit, second deposit, withdrawal
    
    def test_trading_operations(self):
        """Test trading operations."""
        # Get stock price
        symbol = "AAPL"
        price = price_service.get_current_price(symbol)
        self.assertIsNotNone(price)
        
        # Calculate how many shares to buy with half the balance
        balance = financial_manager.get_balance(self.user_id)
        amount_to_spend = balance / 2
        quantity = int(amount_to_spend / price)
        
        # Buy shares
        result = trading_manager.buy_shares(self.user_id, symbol, quantity)
        self.assertIsNotNone(result)
        
        # Check holdings
        holdings = portfolio_manager.get_holdings(self.user_id)
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]['symbol'], symbol)
        self.assertEqual(holdings[0]['quantity'], quantity)
        
        # Get portfolio summary
        summary = portfolio_manager.get_portfolio_summary(self.user_id)
        self.assertIsNotNone(summary)
        
        # Sell half the shares
        sell_quantity = quantity // 2
        result = trading_manager.sell_shares(self.user_id, symbol, sell_quantity)
        self.assertIsNotNone(result)
        
        # Check updated holdings
        holdings = portfolio_manager.get_holdings(self.user_id)
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]['symbol'], symbol)
        self.assertEqual(holdings[0]['quantity'], quantity - sell_quantity)
        
        # Test trade history
        trades = trading_manager.get_trade_history(self.user_id)
        self.assertEqual(len(trades), 2)  # One buy, one sell

if __name__ == "__main__":
    unittest.main()
