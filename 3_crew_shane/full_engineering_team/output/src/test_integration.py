#!/usr/bin/env python
# Integration tests for the Trading Simulation Platform

import unittest
from app import platform
from user_management import UserAlreadyExistsError, UserNotFoundError, AuthenticationError
from financial import InvalidAmountError, InsufficientFundsError
from trading import InvalidQuantityError, InsufficientSharesError
from price_service import InvalidSymbolError
import os

class TradingPlatformIntegrationTest(unittest.TestCase):
    """Integration tests for the Trading Simulation Platform"""
    
    @classmethod
    def setUpClass(cls):
        """Set up for all tests"""
        # Use a test database
        import database
        database.db.db_path = "test_trading_platform.db"
        
        # Clear the test database if it exists
        if os.path.exists(database.db.db_path):
            os.remove(database.db.db_path)
        
        # Initialize the database with tables
        database.db._create_tables()
    
    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests"""
        # Clean up the test database
        import database
        if os.path.exists(database.db.db_path):
            os.remove(database.db.db_path)
    
    def setUp(self):
        """Set up for each test"""
        # Make sure we're logged out before each test
        platform.logout()
    
    def test_user_registration_and_login(self):
        """Test user registration and login process"""
        username = "test_user"
        password = "test_password"
        email = "test@example.com"
        
        # Register a new user
        user_id = platform.register_user(username, password, email)
        self.assertTrue(user_id)
        
        # Try to register the same user again (should fail)
        with self.assertRaises(UserAlreadyExistsError):
            platform.register_user(username, password, email)
        
        # Login with correct credentials
        self.assertTrue(platform.login(username, password))
        
        # Login with incorrect credentials
        platform.logout()
        with self.assertRaises(AuthenticationError):
            platform.login(username, "wrong_password")
        
        # Login with non-existent user
        with self.assertRaises(UserNotFoundError):
            platform.login("nonexistent_user", "password")
    
    def test_account_funding_and_balance(self):
        """Test account funding and balance checking"""
        username = "finance_user"
        password = "finance_password"
        
        # Register and login
        platform.register_user(username, password)
        platform.login(username, password)
        
        # Initial balance should be 0
        self.assertEqual(platform.check_balance(), 0.0)
        
        # Deposit funds
        platform.deposit_funds(1000, "Test deposit")
        self.assertEqual(platform.check_balance(), 1000.0)
        
        # Try to deposit negative amount
        with self.assertRaises(InvalidAmountError):
            platform.deposit_funds(-100)
        
        # Withdraw funds
        platform.withdraw_funds(500, "Test withdrawal")
        self.assertEqual(platform.check_balance(), 500.0)
        
        # Try to withdraw negative amount
        with self.assertRaises(InvalidAmountError):
            platform.withdraw_funds(-100)
        
        # Try to withdraw more than available balance
        with self.assertRaises(InsufficientFundsError):
            platform.withdraw_funds(1000)
    
    def test_stock_trading(self):
        """Test buying and selling stocks"""
        username = "trader_user"
        password = "trader_password"
        
        # Register and login
        platform.register_user(username, password)
        platform.login(username, password)
        
        # Fund account
        platform.deposit_funds(10000, "Trading funds")
        
        # Buy stocks
        buy_transaction = platform.buy_stock("AAPL", 10)
        self.assertEqual(buy_transaction["symbol"], "AAPL")
        self.assertEqual(buy_transaction["quantity"], 10)
        
        # Check portfolio
        portfolio = platform.get_portfolio()
        self.assertGreater(portfolio["holdings_value"], 0)
        self.assertEqual(len(portfolio["holdings"]), 1)
        
        # Try to buy with invalid quantity
        with self.assertRaises(InvalidQuantityError):
            platform.buy_stock("MSFT", -5)
        
        # Try to buy with insufficient funds
        large_quantity = 1000
        with self.assertRaises(InsufficientFundsError):
            platform.buy_stock("GOOGL", large_quantity)
        
        # Try to buy invalid symbol
        with self.assertRaises(InvalidSymbolError):
            platform.buy_stock("INVALID", 1)
        
        # Sell stocks
        sell_transaction = platform.sell_stock("AAPL", 5)
        self.assertEqual(sell_transaction["symbol"], "AAPL")
        self.assertEqual(sell_transaction["quantity"], 5)
        self.assertEqual(sell_transaction["remaining_shares"], 5)
        
        # Try to sell more than owned
        with self.assertRaises(InsufficientSharesError):
            platform.sell_stock("AAPL", 10)
        
        # Sell all remaining shares
        platform.sell_stock("AAPL", 5)
        
        # Portfolio should now be empty of holdings
        portfolio = platform.get_portfolio()
        self.assertEqual(len(portfolio["holdings"]), 0)
    
    def test_transaction_history(self):
        """Test transaction history functionality"""
        username = "history_user"
        password = "history_password"
        
        # Register and login
        platform.register_user(username, password)
        platform.login(username, password)
        
        # Perform some transactions
        platform.deposit_funds(5000, "Initial deposit")
        platform.buy_stock("MSFT", 3)
        platform.sell_stock("MSFT", 1)
        platform.withdraw_funds(500, "Test withdrawal")
        
        # Get transaction history
        transactions = platform.get_transaction_history()
        self.assertEqual(len(transactions), 4)
        
        # Test filtering by type
        buy_transactions = platform.get_transaction_history(transaction_type="buy")
        self.assertEqual(len(buy_transactions), 1)
        
        sell_transactions = platform.get_transaction_history(transaction_type="sell")
        self.assertEqual(len(sell_transactions), 1)
        
        deposit_transactions = platform.get_transaction_history(transaction_type="deposit")
        self.assertEqual(len(deposit_transactions), 1)
        
        withdrawal_transactions = platform.get_transaction_history(transaction_type="withdrawal")
        self.assertEqual(len(withdrawal_transactions), 1)
    
    def test_portfolio_calculation(self):
        """Test portfolio calculation functionality"""
        username = "portfolio_user"
        password = "portfolio_password"
        
        # Register and login
        platform.register_user(username, password)
        platform.login(username, password)
        
        # Fund account
        platform.deposit_funds(20000, "Portfolio test funds")
        
        # Buy multiple stocks
        platform.buy_stock("AAPL", 10)
        platform.buy_stock("MSFT", 8)
        platform.buy_stock("GOOGL", 2)
        
        # Check portfolio
        portfolio = platform.get_portfolio()
        self.assertEqual(len(portfolio["holdings"]), 3)
        
        # Check profit/loss calculation
        profit_loss = platform.get_profit_loss()
        self.assertIn("unrealized_gain_loss", profit_loss)
        self.assertIn("realized_gain_loss", profit_loss)
        self.assertIn("total_gain_loss", profit_loss)

if __name__ == "__main__":
    unittest.main()
