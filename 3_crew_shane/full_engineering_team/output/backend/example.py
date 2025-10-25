import logging
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from backend.database import initialize_database, reset_database
from backend.app import create_app
from backend.api import CustomJSONEncoder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pretty_print(data):
    """
    Prints data in a formatted JSON way.
    
    Args:
        data: The data to print
    """
    print(json.dumps(data, indent=2, cls=CustomJSONEncoder))

def run_example():
    """
    Runs a comprehensive example of the trading platform.
    """
    logger.info("Starting Trading Simulation Platform Example")
    
    # Reset database for clean example
    logger.info("Resetting database for clean example...")
    reset_database()
    
    # Create app instance
    app = create_app()
    
    # Step 1: Create users
    print("\n==== Creating Users ====")
    alice = app.api.register_user("alice", "password123", "alice@example.com")
    bob = app.api.register_user("bob", "password123", "bob@example.com")
    
    print("Alice's account:")
    pretty_print(alice)
    
    print("\nBob's account:")
    pretty_print(bob)
    
    # Step 2: Login
    print("\n==== User Login ====")
    alice_login = app.api.login("alice", "password123")
    print("Alice's login:")
    pretty_print(alice_login)
    
    # Get user IDs
    alice_id = alice["user_id"]
    bob_id = bob["user_id"]
    
    # Step 3: Add funds
    print("\n==== Adding Funds ====")
    alice_deposit = app.api.deposit_funds(alice_id, 10000, "Initial deposit")
    bob_deposit = app.api.deposit_funds(bob_id, 15000, "Initial deposit")
    
    print("Alice's deposit:")
    pretty_print(alice_deposit)
    
    print("\nBob's deposit:")
    pretty_print(bob_deposit)
    
    # Step 4: Get available stocks
    print("\n==== Available Stocks ====")
    stocks = app.api.get_available_stocks()
    pretty_print(stocks)
    
    # Step 5: Get stock prices
    print("\n==== Stock Prices ====")
    apple_price = app.api.get_stock_price("AAPL")
    microsoft_price = app.api.get_stock_price("MSFT")
    
    print("Apple stock price:")
    pretty_print(apple_price)
    
    print("\nMicrosoft stock price:")
    pretty_print(microsoft_price)
    
    # Step 6: Buy stocks
    print("\n==== Buying Stocks ====")
    # Alice buys Apple and Microsoft
    alice_buy_aapl = app.api.buy_stock(alice_id, "AAPL", 10)
    alice_buy_msft = app.api.buy_stock(alice_id, "MSFT", 5)
    
    # Bob buys Google and Amazon
    bob_buy_googl = app.api.buy_stock(bob_id, "GOOGL", 2)
    bob_buy_amzn = app.api.buy_stock(bob_id, "AMZN", 3)
    
    print("Alice buys Apple:")
    pretty_print(alice_buy_aapl)
    
    print("\nBob buys Google:")
    pretty_print(bob_buy_googl)
    
    # Step 7: Check balances
    print("\n==== Account Balances ====")
    alice_balance = app.api.get_account_balance(alice_id)
    bob_balance = app.api.get_account_balance(bob_id)
    
    print("Alice's balance:")
    pretty_print(alice_balance)
    
    print("\nBob's balance:")
    pretty_print(bob_balance)
    
    # Step 8: Check portfolios
    print("\n==== Portfolios ====")
    alice_portfolio = app.api.get_portfolio(alice_id)
    bob_portfolio = app.api.get_portfolio(bob_id)
    
    print("Alice's portfolio:")
    pretty_print(alice_portfolio)
    
    print("\nBob's portfolio:")
    pretty_print(bob_portfolio)
    
    # Step 9: Sell some stocks
    print("\n==== Selling Stocks ====")
    alice_sell_aapl = app.api.sell_stock(alice_id, "AAPL", 5)  # Sell half of Apple shares
    
    print("Alice sells 5 Apple shares:")
    pretty_print(alice_sell_aapl)
    
    # Step 10: Check updated portfolio
    print("\n==== Updated Portfolio ====")
    alice_updated_portfolio = app.api.get_portfolio(alice_id)
    
    print("Alice's updated portfolio:")
    pretty_print(alice_updated_portfolio)
    
    # Step 11: Get transaction history
    print("\n==== Transaction History ====")
    alice_transactions = app.api.get_transaction_history(alice_id)
    
    print("Alice's transactions:")
    pretty_print(alice_transactions)
    
    # Step 12: Get trade history
    print("\n==== Trade History ====")
    alice_trades = app.api.get_activity_feed(alice_id)
    
    print("Alice's activity feed:")
    pretty_print(alice_trades)
    
    # Step 13: Historical data
    print("\n==== Historical Stock Data ====")
    aapl_history = app.api.get_stock_history("AAPL", days=7)  # Just a week for brevity
    
    print("Apple stock history (7 days):")
    pretty_print(aapl_history)
    
    # Step 14: Portfolio performance
    print("\n==== Portfolio Performance ====")
    alice_performance = app.api.get_portfolio_performance(alice_id, days=7)
    
    print("Alice's portfolio performance (7 days):")
    pretty_print(alice_performance)
    
    logger.info("Example completed successfully")


if __name__ == "__main__":
    run_example()