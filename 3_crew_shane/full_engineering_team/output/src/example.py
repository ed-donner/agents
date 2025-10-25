#!/usr/bin/env python
# Example usage of the Trading Simulation Platform

from app import platform
from user_management import UserAlreadyExistsError, UserNotFoundError, AuthenticationError
from financial import InvalidAmountError, InsufficientFundsError
from trading import InvalidQuantityError, InsufficientSharesError
from price_service import InvalidSymbolError
import time

def run_example():
    """Run a complete example of the trading platform"""
    print("=== Trading Simulation Platform Demo ===")
    print("This demo will walk through the main features of the platform.\n")
    
    # 1. User Registration and Login
    print("\n=== User Registration and Login ===")
    username = "demo_user"
    password = "demo_password"
    
    try:
        platform.register_user(username, password, email="demo@example.com")
    except UserAlreadyExistsError:
        print(f"User {username} already exists. Proceeding with login.")
    
    try:
        platform.login(username, password)
    except (UserNotFoundError, AuthenticationError) as e:
        print(f"Login failed: {e}")
        return
    
    # 2. Account Funding
    print("\n=== Account Funding ===")
    try:
        platform.deposit_funds(10000, "Initial deposit")
        balance = platform.check_balance()
        print(f"Successfully funded account with $10,000. Current balance: ${balance:.2f}")
    except InvalidAmountError as e:
        print(f"Funding failed: {e}")
        return
    
    # 3. View Available Stocks
    print("\n=== Available Stocks ===")
    available_stocks = platform.get_available_stocks()
    
    # 4. Check Stock Prices
    print("\n=== Checking Stock Prices ===")
    try:
        for symbol in ["AAPL", "MSFT", "GOOGL"]:
            price = platform.get_stock_price(symbol)
            print(f"{symbol} current price: ${price:.2f}")
    except InvalidSymbolError as e:
        print(f"Error checking prices: {e}")
    
    # 5. Buy Stocks
    print("\n=== Buying Stocks ===")
    try:
        # Buy Apple shares
        platform.buy_stock("AAPL", 10)
        # Buy Microsoft shares
        platform.buy_stock("MSFT", 5)
        # Buy Google shares
        platform.buy_stock("GOOGL", 2)
    except (InvalidQuantityError, InsufficientFundsError, InvalidSymbolError) as e:
        print(f"Error buying stocks: {e}")
    
    # 6. View Portfolio
    print("\n=== Viewing Portfolio ===")
    portfolio = platform.get_portfolio()
    
    # 7. Sell Some Shares
    print("\n=== Selling Shares ===")
    try:
        # Sell some Apple shares
        platform.sell_stock("AAPL", 3)
    except (InvalidQuantityError, InsufficientSharesError, InvalidSymbolError) as e:
        print(f"Error selling stocks: {e}")
    
    # 8. View Updated Portfolio
    print("\n=== Updated Portfolio ===")
    updated_portfolio = platform.get_portfolio()
    
    # 9. View Profit/Loss
    print("\n=== Profit/Loss ===")
    profit_loss = platform.get_profit_loss()
    
    # 10. Transaction History
    print("\n=== Transaction History ===")
    transactions = platform.get_transaction_history(limit=10)
    
    # 11. Withdraw Funds
    print("\n=== Withdrawing Funds ===")
    try:
        platform.withdraw_funds(1000, "Demo withdrawal")
    except (InvalidAmountError, InsufficientFundsError) as e:
        print(f"Error withdrawing funds: {e}")
    
    # 12. Final Balance
    print("\n=== Final Account Status ===")
    final_balance = platform.check_balance()
    final_portfolio = platform.get_portfolio()
    
    # 13. Logout
    print("\n=== Logging Out ===")
    platform.logout()
    
    print("\n=== Demo Complete ===")
    print("The demo has completed successfully!")
    print("You've seen the core functionality of the Trading Simulation Platform.")

if __name__ == "__main__":
    run_example()
