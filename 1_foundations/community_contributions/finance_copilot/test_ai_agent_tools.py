#!/usr/bin/env python3
"""
Comprehensive test suite for Finance Copilot AI Agent Tools
Tests all available tools to ensure they're working correctly
"""

import unittest
import json
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agent import FinanceCopilotAgent
from config import Config


class TestFinanceCopilotAgentTools(unittest.TestCase):
    """Test suite for all AI Agent tools"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the config to use our temp database
        with patch('ai_agent.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.DATABASE_PATH = self.temp_db.name
            mock_config.ALPHA_VANTAGE_API_KEY = 'test_key'
            mock_config.OPENAI_API_KEY = 'test_openai_key'
            mock_config.PUSHOVER_USER_KEY = 'test_user_key'
            mock_config.PUSHOVER_APP_TOKEN = 'test_app_token'
            mock_config.STOCK_SYMBOLS = ['AAPL', 'GOOGL']
            mock_config.CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD']
            mock_config.DEFAULT_RISK_PROFILE = 'moderate'
            mock_config.DEFAULT_ALERT_THRESHOLD = 0.05
            mock_config.MONTE_CARLO_SIMULATIONS = 1000
            mock_config.FORECAST_YEARS = 2
            mock_config.ENABLE_PUSH_NOTIFICATIONS = True
            mock_config.ENABLE_EMAIL_NOTIFICATIONS = False
            
            mock_config_class.return_value = mock_config
            
            # Initialize the agent
            self.agent = FinanceCopilotAgent()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_agent_initialization(self):
        """Test that the agent initializes correctly with all tools"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.tools)
        self.assertGreater(len(self.agent.tools), 0)
        
        # Check that all expected tools are present
        tool_names = [tool.name for tool in self.agent.tools]
        expected_tools = [
            'get_stock_price',
            'get_crypto_price', 
            'get_stock_fundamentals',
            'get_company_news',
            'get_portfolio',
            'add_portfolio_item',
            'update_portfolio',
            'calculate_portfolio_metrics',
            'run_monte_carlo_simulation',
            'create_portfolio_charts',
            'suggest_rebalancing',
            'add_price_alert',
            'get_market_summary',
            'send_notification'
        ]
        
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names, f"Tool {tool_name} not found")
    
    def test_get_stock_price_tool(self):
        """Test the get_stock_price tool"""
        # Mock the market data response
        mock_response = {
            "symbol": "AAPL",
            "price": 150.00,
            "change": 2.50,
            "change_percent": 1.69,
            "volume": 1000000,
            "market_cap": 2500000000000
        }
        
        with patch.object(self.agent.market_data, 'get_stock_price', return_value=mock_response):
            result = self.agent._get_stock_price("AAPL")
            
            # Parse the JSON result
            parsed_result = json.loads(result)
            
            self.assertEqual(parsed_result["symbol"], "AAPL")
            self.assertEqual(parsed_result["price"], 150.00)
            self.assertIn("change", parsed_result)
    
    def test_get_stock_price_tool_error(self):
        """Test the get_stock_price tool with error handling"""
        error_response = {"error": "Symbol not found"}
        
        with patch.object(self.agent.market_data, 'get_stock_price', return_value=error_response):
            result = self.agent._get_stock_price("INVALID")
            
            self.assertIn("Error:", result)
            self.assertIn("Symbol not found", result)
    
    def test_get_crypto_price_tool(self):
        """Test the get_crypto_price tool"""
        mock_response = {
            "symbol": "BTC-USD",
            "price": 45000.00,
            "change": 500.00,
            "change_percent": 1.12,
            "volume": 50000000000,
            "market_cap": 850000000000
        }
        
        with patch.object(self.agent.market_data, 'get_crypto_price', return_value=mock_response):
            result = self.agent._get_crypto_price("BTC-USD")
            
            parsed_result = json.loads(result)
            
            self.assertEqual(parsed_result["symbol"], "BTC-USD")
            self.assertEqual(parsed_result["price"], 45000.00)
            self.assertIn("change", parsed_result)
    
    def test_get_stock_fundamentals_tool(self):
        """Test the get_stock_fundamentals tool"""
        mock_response = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 2500000000000,
            "pe_ratio": 25.5,
            "price_to_book": 15.2,
            "dividend_yield": 0.5,
            "return_on_equity": 0.15,
            "debt_to_equity": 0.8
        }
        
        with patch.object(self.agent.market_data, 'get_stock_fundamentals', return_value=mock_response):
            result = self.agent._get_stock_fundamentals("AAPL")
            
            parsed_result = json.loads(result)
            
            self.assertEqual(parsed_result["symbol"], "AAPL")
            self.assertEqual(parsed_result["company_name"], "Apple Inc.")
            self.assertIn("pe_ratio", parsed_result)
            self.assertIn("market_cap", parsed_result)
    
    def test_get_stock_fundamentals_tool_error(self):
        """Test the get_stock_fundamentals tool with error handling"""
        error_response = {"error": "Failed to fetch fundamentals"}
        
        with patch.object(self.agent.market_data, 'get_stock_fundamentals', return_value=error_response):
            result = self.agent._get_stock_fundamentals("INVALID")
            
            self.assertIn("Error:", result)
            self.assertIn("Failed to fetch fundamentals", result)
    
    def test_get_company_news_tool(self):
        """Test the get_company_news tool"""
        mock_response = [
            {
                "title": "Apple Reports Strong Q4 Earnings",
                "summary": "Apple Inc. reported better-than-expected quarterly earnings...",
                "url": "https://example.com/news1",
                "published": "2024-01-15T10:00:00",
                "sentiment": "positive",
                "sentiment_score": 0.8
            },
            {
                "title": "New iPhone Model Announced",
                "summary": "Apple unveiled its latest iPhone model...",
                "url": "https://example.com/news2",
                "published": "2024-01-14T15:30:00",
                "sentiment": "neutral",
                "sentiment_score": 0.1
            }
        ]
        
        with patch.object(self.agent.market_data, 'get_company_news', return_value=mock_response):
            result = self.agent._get_company_news("AAPL", limit=2)
            
            parsed_result = json.loads(result)
            
            self.assertEqual(len(parsed_result), 2)
            self.assertEqual(parsed_result[0]["title"], "Apple Reports Strong Q4 Earnings")
            self.assertIn("sentiment", parsed_result[0])
    
    def test_get_portfolio_tool_empty(self):
        """Test the get_portfolio tool with empty portfolio"""
        # Mock empty portfolio
        with patch.object(self.agent.db, 'get_portfolio', return_value=pd.DataFrame()):
            result = self.agent._get_portfolio()
            
            self.assertEqual(result, "Portfolio is empty")
    
    def test_get_portfolio_tool_with_data(self):
        """Test the get_portfolio tool with portfolio data"""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50],
            'avg_price': [150.00, 2800.00],
            'purchase_date': ['2024-01-01', '2024-01-02']
        })
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data):
            result = self.agent._get_portfolio()
            
            self.assertIn("AAPL", result)
            self.assertIn("GOOGL", result)
            self.assertIn("100", result)
            self.assertIn("150.00", result)
    
    def test_add_portfolio_item_tool(self):
        """Test the add_portfolio_item tool"""
        with patch.object(self.agent.db, 'add_portfolio_item') as mock_add:
            result = self.agent._add_portfolio_item("AAPL", 100, 150.00, "2024-01-01")
            
            mock_add.assert_called_once_with("AAPL", 100, 150.00, "2024-01-01")
            self.assertIn("Successfully added", result)
            self.assertIn("100 shares of AAPL", result)
    
    def test_update_portfolio_tool(self):
        """Test the update_portfolio tool"""
        with patch.object(self.agent.db, 'update_portfolio') as mock_update:
            result = self.agent._update_portfolio("AAPL", 50, 160.00, "BUY")
            
            mock_update.assert_called_once_with("AAPL", 50, 160.00, "BUY")
            self.assertIn("Successfully bought", result)
            self.assertIn("50 shares of AAPL", result)
    
    def test_calculate_portfolio_metrics_tool_empty(self):
        """Test the calculate_portfolio_metrics tool with empty portfolio"""
        with patch.object(self.agent.db, 'get_portfolio', return_value=pd.DataFrame()):
            result = self.agent._calculate_portfolio_metrics()
            
            self.assertEqual(result, "Portfolio is empty")
    
    def test_calculate_portfolio_metrics_tool_with_data(self):
        """Test the calculate_portfolio_metrics tool with portfolio data"""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50],
            'avg_price': [150.00, 2800.00]
        })
        
        current_prices = {'AAPL': 160.00, 'GOOGL': 2900.00}
        
        mock_metrics = {
            "total_value": 161000.00,
            "total_cost": 155000.00,
            "total_pnl": 6000.00,
            "total_return": 0.0387,
            "sharpe_ratio": 1.25,
            "max_drawdown": -0.05
        }
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data), \
             patch.object(self.agent.market_data, 'get_portfolio_prices', return_value=current_prices), \
             patch.object(self.agent.analysis_tool, 'calculate_portfolio_metrics', return_value=mock_metrics):
            
            result = self.agent._calculate_portfolio_metrics()
            
            # Parse the JSON result
            parsed_result = json.loads(result)
            
            self.assertEqual(parsed_result["total_value"], 161000.00)
            self.assertEqual(parsed_result["total_pnl"], 6000.00)
            self.assertIn("sharpe_ratio", parsed_result)
    
    def test_run_monte_carlo_simulation_tool_empty(self):
        """Test the run_monte_carlo_simulation tool with empty portfolio"""
        with patch.object(self.agent.db, 'get_portfolio', return_value=pd.DataFrame()):
            result = self.agent._run_monte_carlo_simulation()
            
            self.assertEqual(result, "Portfolio is empty")
    
    def test_run_monte_carlo_simulation_tool_with_data(self):
        """Test the run_monte_carlo_simulation tool with portfolio data"""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50]
        })
        
        returns_data = {
            'AAPL': pd.Series([0.01, -0.02, 0.03, -0.01, 0.02]),
            'GOOGL': pd.Series([0.02, -0.01, 0.01, 0.03, -0.02])
        }
        
        mock_simulation = {
            "forecast_years": 2,
            "num_simulations": 1000,
            "expected_return": 0.08,
            "volatility": 0.15,
            "confidence_intervals": {
                "5%": 0.02,
                "25%": 0.05,
                "50%": 0.08,
                "75%": 0.11,
                "95%": 0.14
            }
        }
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data), \
             patch.object(self.agent.market_data, 'get_historical_data') as mock_hist, \
             patch.object(self.agent.analysis_tool, 'calculate_returns') as mock_returns, \
             patch.object(self.agent.analysis_tool, 'run_monte_carlo_simulation', return_value=mock_simulation):
            
            # Mock historical data returns
            mock_hist.return_value = pd.DataFrame({'Close': [100, 101, 99, 102, 104]})
            mock_returns.return_value = pd.Series([0.01, -0.02, 0.03, 0.02])
            
            result = self.agent._run_monte_carlo_simulation(forecast_years=2, num_simulations=1000)
            
            parsed_result = json.loads(result)
            
            self.assertEqual(parsed_result["forecast_years"], 2)
            self.assertEqual(parsed_result["expected_return"], 0.08)
            self.assertIn("confidence_intervals", parsed_result)
    
    def test_create_portfolio_charts_tool(self):
        """Test the create_portfolio_charts tool"""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50],
            'avg_price': [150.00, 2800.00]
        })
        
        current_prices = {'AAPL': 160.00, 'GOOGL': 2900.00}
        
        mock_charts = {
            "total_value": 161000.00,
            "symbols": ["AAPL", "GOOGL"],
            "weights": [0.35, 0.65],
            "returns": [0.067, 0.036]
        }
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data), \
             patch.object(self.agent.market_data, 'get_portfolio_prices', return_value=current_prices), \
             patch.object(self.agent.analysis_tool, 'create_portfolio_charts', return_value=mock_charts):
            
            result = self.agent._create_portfolio_charts()
            
            # Parse the JSON result
            parsed_result = json.loads(result)
            
            self.assertIn("total_value", parsed_result)
            self.assertIn("symbols", parsed_result)
            self.assertIn("weights", parsed_result)
            self.assertIn("returns", parsed_result)
            self.assertEqual(parsed_result["total_value"], 161000.00)
    
    def test_suggest_rebalancing_tool(self):
        """Test the suggest_rebalancing tool"""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50],
            'avg_price': [150.00, 2800.00]
        })
        
        current_prices = {'AAPL': 160.00, 'GOOGL': 2900.00}
        
        mock_rebalancing = {
            "current_allocation": {"AAPL": 0.35, "GOOGL": 0.65},
            "target_allocation": {"AAPL": 0.50, "GOOGL": 0.50},
            "actions": [
                {"symbol": "AAPL", "action": "BUY", "shares": 25, "reason": "Underweight"},
                {"symbol": "GOOGL", "action": "SELL", "shares": 15, "reason": "Overweight"}
            ]
        }
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data), \
             patch.object(self.agent.market_data, 'get_portfolio_prices', return_value=current_prices), \
             patch.object(self.agent.analysis_tool, 'suggest_rebalancing', return_value=mock_rebalancing):
            
            result = self.agent._suggest_rebalancing()
            
            parsed_result = json.loads(result)
            
            self.assertIn("current_allocation", parsed_result)
            self.assertIn("target_allocation", parsed_result)
            self.assertIn("actions", parsed_result)
            self.assertEqual(len(parsed_result["actions"]), 2)
    
    def test_add_price_alert_tool(self):
        """Test the add_price_alert tool"""
        with patch.object(self.agent.db, 'add_alert') as mock_add_alert:
            result = self.agent._add_price_alert("AAPL", "PRICE_DROP", 160.00)
            
            mock_add_alert.assert_called_once_with("AAPL", "PRICE_DROP", 160.00)
            self.assertIn("Successfully added", result)
            self.assertIn("AAPL", result)
    
    def test_get_market_summary_tool(self):
        """Test the get_market_summary tool"""
        mock_summary = {
            "^GSPC": {"symbol": "^GSPC", "price": 4500.00, "change": 25.00},
            "^DJI": {"symbol": "^DJI", "price": 35000.00, "change": 150.00},
            "^IXIC": {"symbol": "^IXIC", "price": 14000.00, "change": 75.00}
        }
        
        with patch.object(self.agent.market_data, 'get_market_summary', return_value=mock_summary):
            result = self.agent._get_market_summary()
            
            parsed_result = json.loads(result)
            
            self.assertIn("^GSPC", parsed_result)
            self.assertIn("^DJI", parsed_result)
            self.assertIn("^IXIC", parsed_result)
            self.assertEqual(parsed_result["^GSPC"]["price"], 4500.00)
    
    def test_send_notification_tool(self):
        """Test the send_notification tool"""
        with patch.object(self.agent.notification_system, 'send_pushover_notification') as mock_send:
            mock_send.return_value = True
            result = self.agent._send_notification("Test title", "Test message")
            
            mock_send.assert_called_once_with("Test title", "Test message")
            self.assertIn("Successfully sent notification", result)
    
    def test_tool_error_handling(self):
        """Test that all tools handle errors gracefully"""
        # Test with a tool that might fail
        with patch.object(self.agent.market_data, 'get_stock_price', side_effect=Exception("Network error")):
            result = self.agent._get_stock_price("AAPL")
            
            self.assertIn("Error:", result)
            self.assertIn("Network error", result)
    
    def test_tool_parameter_validation(self):
        """Test that tools validate parameters correctly"""
        # Test with invalid parameters
        result = self.agent._get_stock_price("")  # Empty symbol
        
        self.assertIn("Error:", result)
    
    def test_tool_integration(self):
        """Test that tools work together correctly"""
        # Add a portfolio item
        with patch.object(self.agent.db, 'add_portfolio_item'):
            add_result = self.agent._add_portfolio_item("AAPL", 100, 150.00)
            self.assertIn("Successfully added", add_result)
        
        # Get portfolio
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL'],
            'shares': [100],
            'avg_price': [150.00]
        })
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data):
            portfolio_result = self.agent._get_portfolio()
            self.assertIn("AAPL", portfolio_result)
            self.assertIn("100", portfolio_result)


class TestFinanceCopilotAgentIntegration(unittest.TestCase):
    """Integration tests for the Finance Copilot Agent"""
    
    def setUp(self):
        """Set up test fixtures for integration tests"""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the config
        with patch('ai_agent.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.DATABASE_PATH = self.temp_db.name
            mock_config.ALPHA_VANTAGE_API_KEY = 'test_key'
            mock_config.OPENAI_API_KEY = 'test_openai_key'
            mock_config.PUSHOVER_USER_KEY = 'test_user_key'
            mock_config.PUSHOVER_APP_TOKEN = 'test_app_token'
            mock_config.STOCK_SYMBOLS = ['AAPL', 'GOOGL']
            mock_config.CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD']
            mock_config.DEFAULT_RISK_PROFILE = 'moderate'
            mock_config.DEFAULT_ALERT_THRESHOLD = 0.05
            mock_config.MONTE_CARLO_SIMULATIONS = 1000
            mock_config.FORECAST_YEARS = 2
            mock_config.ENABLE_PUSH_NOTIFICATIONS = True
            mock_config.ENABLE_EMAIL_NOTIFICATIONS = False
            
            mock_config_class.return_value = mock_config
            
            self.agent = FinanceCopilotAgent()
    
    def tearDown(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_full_portfolio_workflow(self):
        """Test a complete portfolio management workflow"""
        # 1. Add portfolio items
        with patch.object(self.agent.db, 'add_portfolio_item'):
            self.agent._add_portfolio_item("AAPL", 100, 150.00)
            self.agent._add_portfolio_item("GOOGL", 50, 2800.00)
        
        # 2. Get portfolio
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'shares': [100, 50],
            'avg_price': [150.00, 2800.00]
        })
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data):
            portfolio_result = self.agent._get_portfolio()
            self.assertIn("AAPL", portfolio_result)
            self.assertIn("GOOGL", portfolio_result)
        
        # 3. Calculate metrics
        current_prices = {'AAPL': 160.00, 'GOOGL': 2900.00}
        mock_metrics = {
            "total_value": 161000.00,
            "total_cost": 155000.00,
            "total_pnl": 6000.00,
            "total_return": 0.0387
        }
        
        with patch.object(self.agent.db, 'get_portfolio', return_value=portfolio_data), \
             patch.object(self.agent.market_data, 'get_portfolio_prices', return_value=current_prices), \
             patch.object(self.agent.analysis_tool, 'calculate_portfolio_metrics', return_value=mock_metrics):
            
            metrics_result = self.agent._calculate_portfolio_metrics()
            
            parsed_metrics = json.loads(metrics_result)
            
            self.assertEqual(parsed_metrics["total_pnl"], 6000.00)
            self.assertEqual(parsed_metrics["total_return"], 0.0387)
    
    def test_market_data_integration(self):
        """Test market data tools working together"""
        # Mock market data responses
        stock_data = {
            "symbol": "AAPL",
            "price": 150.00,
            "change": 2.50,
            "change_percent": 1.69
        }
        
        fundamentals_data = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "pe_ratio": 25.5,
            "market_cap": 2500000000000
        }
        
        news_data = [
            {
                "title": "Apple Reports Strong Earnings",
                "sentiment": "positive",
                "sentiment_score": 0.8
            }
        ]
        
        with patch.object(self.agent.market_data, 'get_stock_price', return_value=stock_data), \
             patch.object(self.agent.market_data, 'get_stock_fundamentals', return_value=fundamentals_data), \
             patch.object(self.agent.market_data, 'get_company_news', return_value=news_data):
            
            # Test stock price
            price_result = self.agent._get_stock_price("AAPL")
            price_data = json.loads(price_result)
            self.assertEqual(price_data["price"], 150.00)
            
            # Test fundamentals
            fund_result = self.agent._get_stock_fundamentals("AAPL")
            fund_data = json.loads(fund_result)
            self.assertEqual(fund_data["pe_ratio"], 25.5)
            
            # Test news
            news_result = self.agent._get_company_news("AAPL", limit=1)
            news_data_result = json.loads(news_result)
            self.assertEqual(len(news_data_result), 1)
            self.assertEqual(news_data_result[0]["sentiment"], "positive")


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_suite.addTest(unittest.makeSuite(TestFinanceCopilotAgentTools))
    test_suite.addTest(unittest.makeSuite(TestFinanceCopilotAgentIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(len(result.failures) + len(result.errors))
