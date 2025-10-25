#!/usr/bin/env python3
import logging
import sys
from backend.user_management import user_manager
from backend.financial import financial_manager
from backend.trading import trading_manager
from backend.portfolio import portfolio_manager
from backend.price_service import price_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Example usage of the trading simulation platform."""
    # Create a user
    username = "test_user"
    password = "password123"
    
    # First check if user already exists
    existing_user = user_manager.get_user_by_username(username)
    if existing_user:
        logger.info(f"User '{username}' already exists with ID {existing_user['id']}")
        user_id = existing_user['id']
    else:
        user = user_manager.create_user(username, password)
        if not user:
            logger.error("Failed to create user")
            return
        
        user_id = user['id']
        logger.info(f"Created user with ID {user_id}")
        
        # Add initial funds
        financial_manager.deposit(user_id, 10000.0, "Initial deposit")
    
    # Get current balance
    balance = financial_manager.get_balance(user_id)
    logger.info(f"Current balance: ${balance:.2f}")
    
    # Get some stock prices
    symbols = ["AAPL", "MSFT", "GOOGL"]
    prices = {}
    
    for symbol in symbols:
        price = price_service.get_current_price(symbol)
        prices[symbol] = price
        logger.info(f"{symbol} price: ${price:.2f}")
    
    # Buy some shares
    symbol = "AAPL"
    quantity = 5
    
    logger.info(f"Buying {quantity} shares of {symbol}...")
    result = trading_manager.buy_shares(user_id, symbol, quantity)
    
    if result:
        logger.info(f"Purchase successful: {quantity} shares of {symbol} at ${result['price']:.2f}")
        logger.info(f"Total cost: ${result['total_cost']:.2f}")
    else:
        logger.error("Purchase failed")
    
    # Get updated balance
    balance = financial_manager.get_balance(user_id)
    logger.info(f"Updated balance: ${balance:.2f}")
    
    # Get portfolio holdings
    holdings = portfolio_manager.get_holdings(user_id)
    logger.info("Current holdings:")
    for holding in holdings:
        logger.info(f"  {holding['symbol']}: {holding['quantity']} shares, "  
                  f"avg price: ${holding['average_price']:.2f}, "  
                  f"current value: ${holding['current_value']:.2f}, "  
                  f"P/L: ${holding['profit_loss']:.2f} ({holding['profit_loss_percent']:.2f}%)")
    
    # Get portfolio summary
    summary = portfolio_manager.get_portfolio_summary(user_id)
    logger.info("Portfolio summary:")
    logger.info(f"  Total value: ${summary['total_value']:.2f}")
    logger.info(f"  Total cost: ${summary['total_cost']:.2f}")
    logger.info(f"  Total P/L: ${summary['total_profit_loss']:.2f} ({summary['total_profit_loss_percent']:.2f}%)")
    
    # Sell some shares
    if holdings and holdings[0]['quantity'] > 0:
        sell_symbol = holdings[0]['symbol']
        sell_quantity = 1
        
        logger.info(f"Selling {sell_quantity} share of {sell_symbol}...")
        result = trading_manager.sell_shares(user_id, sell_symbol, sell_quantity)
        
        if result:
            logger.info(f"Sale successful: {sell_quantity} share of {sell_symbol} at ${result['price']:.2f}")
            logger.info(f"Total proceeds: ${result['total_proceeds']:.2f}")
            logger.info(f"Profit/Loss: ${result['profit_loss']:.2f}")
        else:
            logger.error("Sale failed")
    
    # Get updated balance and holdings
    balance = financial_manager.get_balance(user_id)
    logger.info(f"Final balance: ${balance:.2f}")
    
    holdings = portfolio_manager.get_holdings(user_id)
    logger.info("Final holdings:")
    for holding in holdings:
        logger.info(f"  {holding['symbol']}: {holding['quantity']} shares, "  
                  f"avg price: ${holding['average_price']:.2f}, "  
                  f"current value: ${holding['current_value']:.2f}, "  
                  f"P/L: ${holding['profit_loss']:.2f} ({holding['profit_loss_percent']:.2f}%)")

if __name__ == "__main__":
    main()
