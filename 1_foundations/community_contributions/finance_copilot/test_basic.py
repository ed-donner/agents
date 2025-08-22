#!/usr/bin/env python3
"""
Basic test file for Finance Copilot
Tests core functionality without requiring API keys
"""

import unittest
import tempfile
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import FinanceDatabase

class TestFinanceCopilot(unittest.TestCase):
    """Basic test cases for Finance Copilot"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create config with test database
        self.config = Config()
        self.config.DATABASE_PATH = self.db_path
        
        # Initialize database
        self.db = FinanceDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary database
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables were created
        portfolio = self.db.get_portfolio()
        self.assertIsNotNone(portfolio)
        
        # Check if user preferences were set
        prefs = self.db.get_user_preferences()
        self.assertIn('risk_profile', prefs)
        self.assertIn('alert_threshold', prefs)
    
    def test_portfolio_operations(self):
        """Test portfolio operations"""
        # Add portfolio item
        self.db.add_portfolio_item("AAPL", 100, 150.00)
        
        # Get portfolio
        portfolio = self.db.get_portfolio()
        self.assertEqual(len(portfolio), 1)
        self.assertEqual(portfolio.iloc[0]['symbol'], "AAPL")
        self.assertEqual(portfolio.iloc[0]['shares'], 100)
        self.assertEqual(portfolio.iloc[0]['avg_price'], 150.00)
        
        # Update portfolio (buy more)
        self.db.update_portfolio("AAPL", 50, 160.00, "BUY")
        
        # Check updated portfolio
        portfolio = self.db.get_portfolio()
        self.assertEqual(len(portfolio), 1)
        self.assertEqual(portfolio.iloc[0]['shares'], 150)
        # Average price should be weighted average
        expected_avg = (100 * 150 + 50 * 160) / 150
        self.assertAlmostEqual(portfolio.iloc[0]['avg_price'], expected_avg, places=2)
        
        # Sell some shares
        self.db.update_portfolio("AAPL", 25, 170.00, "SELL")
        
        # Check final portfolio
        portfolio = self.db.get_portfolio()
        self.assertEqual(len(portfolio), 1)
        self.assertEqual(portfolio.iloc[0]['shares'], 125)
    
    def test_transaction_history(self):
        """Test transaction history"""
        # Add portfolio item
        self.db.add_portfolio_item("GOOGL", 10, 2800.00)
        
        # Get transactions
        transactions = self.db.get_transactions()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions.iloc[0]['symbol'], "GOOGL")
        self.assertEqual(transactions.iloc[0]['transaction_type'], "BUY")
        self.assertEqual(transactions.iloc[0]['shares'], 10)
        self.assertEqual(transactions.iloc[0]['price'], 2800.00)
    
    def test_user_preferences(self):
        """Test user preferences"""
        # Set preferences
        self.db.set_user_preferences("aggressive", 0.10)
        
        # Get preferences
        prefs = self.db.get_user_preferences()
        self.assertEqual(prefs['risk_profile'], "aggressive")
        self.assertEqual(prefs['alert_threshold'], 0.10)
    
    def test_alerts(self):
        """Test alert system"""
        # Add alert
        self.db.add_alert("TSLA", "PRICE_DROP", 5.0)
        
        # Get active alerts
        alerts = self.db.get_active_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.iloc[0]['symbol'], "TSLA")
        self.assertEqual(alerts.iloc[0]['alert_type'], "PRICE_DROP")
        self.assertEqual(alerts.iloc[0]['threshold'], 5.0)
        self.assertTrue(alerts.iloc[0]['is_active'])
        
        # Deactivate alert
        alert_id = alerts.iloc[0]['id']
        self.db.deactivate_alert(alert_id)
        
        # Check if alert is deactivated
        alerts = self.db.get_active_alerts()
        self.assertEqual(len(alerts), 0)

class TestConfig(unittest.TestCase):
    """Test configuration class"""
    
    def test_config_defaults(self):
        """Test configuration defaults"""
        config = Config()
        
        # Check default values
        self.assertEqual(config.DEFAULT_RISK_PROFILE, "moderate")
        self.assertEqual(config.DEFAULT_ALERT_THRESHOLD, 0.05)
        self.assertEqual(config.MONTE_CARLO_SIMULATIONS, 10000)
        self.assertEqual(config.FORECAST_YEARS, 5)
        
        # Check that lists are not empty
        self.assertTrue(len(config.STOCK_SYMBOLS) > 0)
        self.assertTrue(len(config.CRYPTO_SYMBOLS) > 0)

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)



