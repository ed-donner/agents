import logging
import os
from .database import initialize_database
from .user_management import UserManagement
from .financial import AccountBalance
from .trading import Trading
from .portfolio import Portfolio
from .transaction_history import TransactionHistory
from .price_service import PriceService
from .api import API

logger = logging.getLogger(__name__)

class TradingApp:
    """
    Main application class that initializes and integrates all modules.
    """
    
    def __init__(self):
        """
        Initialize the trading application.
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Initializing Trading Simulation Platform")
        
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize database
        initialize_database()
        logger.info("Database initialized")
        
        # Initialize API (in a real app, this would start the web server)
        self.api = API
        logger.info("API initialized")
        
        logger.info("Trading Simulation Platform started successfully")
    
    def demo_create_user(self, username, password, email):
        """
        Demo method to create a user account.
        
        Args:
            username (str): The username for the new account
            password (str): The password for the new account
            email (str): The email address for the new account
            
        Returns:
            dict: API response
        """
        return self.api.register_user(username, password, email)
    
    def demo_login(self, username, password):
        """
        Demo method to authenticate a user.
        
        Args:
            username (str): The username to authenticate
            password (str): The password to verify
            
        Returns:
            dict: API response
        """
        return self.api.login(username, password)
    
    def demo_deposit(self, user_id, amount, description="Demo deposit"):
        """
        Demo method to deposit funds.
        
        Args:
            user_id (int): The ID of the user
            amount (float): The amount to deposit
            description (str): Description of the deposit
            
        Returns:
            dict: API response
        """
        return self.api.deposit_funds(user_id, amount, description)
    
    def demo_buy_stock(self, user_id, symbol, quantity):
        """
        Demo method to buy stock.
        
        Args:
            user_id (int): The ID of the user
            symbol (str): The stock symbol
            quantity (int): The number of shares to buy
            
        Returns:
            dict: API response
        """
        return self.api.buy_stock(user_id, symbol, quantity)
    
    def demo_get_portfolio(self, user_id):
        """
        Demo method to get a user's portfolio.
        
        Args:
            user_id (int): The ID of the user
            
        Returns:
            dict: API response
        """
        return self.api.get_portfolio(user_id)
    
    def run_demo(self):
        """
        Run a demonstration of the platform's capabilities.
        
        Returns:
            dict: Demo results
        """
        demo_results = {}
        
        # 1. Create a demo user
        logger.info("Creating demo user...")
        user_result = self.demo_create_user("demo_user", "password123", "demo@example.com")
        demo_results["user_creation"] = user_result
        
        if not user_result["success"]:
            logger.error(f"Demo failed at user creation: {user_result['error']}")
            return demo_results
        
        user_id = user_result["user_id"]
        
        # 2. Login
        logger.info("Logging in...")
        login_result = self.demo_login("demo_user", "password123")
        demo_results["login"] = login_result
        
        if not login_result["success"]:
            logger.error(f"Demo failed at login: {login_result['error']}")
            return demo_results
        
        # 3. Deposit funds
        logger.info("Depositing funds...")
        deposit_result = self.demo_deposit(user_id, 10000, "Initial demo deposit")
        demo_results["deposit"] = deposit_result
        
        if not deposit_result["success"]:
            logger.error(f"Demo failed at deposit: {deposit_result['error']}")
            return demo_results
        
        # 4. Get available stocks
        logger.info("Getting available stocks...")
        stocks_result = self.api.get_available_stocks()
        demo_results["available_stocks"] = stocks_result
        
        if not stocks_result["success"]:
            logger.error(f"Demo failed at getting stocks: {stocks_result['error']}")
            return demo_results
        
        # 5. Buy some stocks
        logger.info("Buying stocks...")
        buy_results = {}
        
        symbols_to_buy = ["AAPL", "MSFT", "GOOGL"]
        quantities = [10, 5, 2]
        
        for symbol, quantity in zip(symbols_to_buy, quantities):
            buy_result = self.demo_buy_stock(user_id, symbol, quantity)
            buy_results[symbol] = buy_result
            
            if not buy_result["success"]:
                logger.error(f"Demo failed at buying {symbol}: {buy_result['error']}")
        
        demo_results["buy_stocks"] = buy_results
        
        # 6. Get portfolio
        logger.info("Getting portfolio...")
        portfolio_result = self.demo_get_portfolio(user_id)
        demo_results["portfolio"] = portfolio_result
        
        # 7. Get portfolio performance
        logger.info("Getting portfolio performance...")
        performance_result = self.api.get_portfolio_performance(user_id)
        demo_results["portfolio_performance"] = performance_result
        
        # 8. Get activity feed
        logger.info("Getting activity feed...")
        activity_result = self.api.get_activity_feed(user_id)
        demo_results["activity_feed"] = activity_result
        
        logger.info("Demo completed successfully")
        return demo_results


# Function to create app instance
def create_app():
    """
    Factory function to create and initialize the application.
    
    Returns:
        TradingApp: Initialized application instance
    """
    return TradingApp()