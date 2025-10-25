import sqlite3
import random
from datetime import datetime, timedelta
from database import db

class PriceServiceError(Exception):
    """Base class for price service errors"""
    pass

class InvalidSymbolError(PriceServiceError):
    """Raised when an invalid stock symbol is provided"""
    pass

class PriceService:
    """Provides stock price information"""
    
    # Dictionary of mock stock data for development/testing
    MOCK_STOCKS = {
        "AAPL": {"name": "Apple Inc.", "base_price": 150.0},
        "MSFT": {"name": "Microsoft Corporation", "base_price": 280.0},
        "GOOGL": {"name": "Alphabet Inc.", "base_price": 2800.0},
        "AMZN": {"name": "Amazon.com, Inc.", "base_price": 3300.0},
        "TSLA": {"name": "Tesla, Inc.", "base_price": 900.0},
        "FB": {"name": "Meta Platforms, Inc.", "base_price": 330.0},
        "NFLX": {"name": "Netflix, Inc.", "base_price": 600.0},
        "V": {"name": "Visa Inc.", "base_price": 220.0},
        "JPM": {"name": "JPMorgan Chase & Co.", "base_price": 160.0},
        "WMT": {"name": "Walmart Inc.", "base_price": 140.0}
    }
    
    @staticmethod
    def get_share_price(symbol):
        """Get the current price for a stock symbol
        
        In a production environment, this would call an external API.
        For simulation, we're using cached prices with random fluctuations.
        
        Args:
            symbol (str): Stock symbol to get price for
            
        Returns:
            float: Current stock price
            
        Raises:
            InvalidSymbolError: If the symbol is not supported
        """
        symbol = symbol.upper()
        
        if symbol not in PriceService.MOCK_STOCKS:
            raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
        
        # Check if we have a recent price in the cache
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT price, last_updated FROM prices WHERE symbol = ?",
                (symbol,)
            )
            cached_price = cursor.fetchone()
            
            now = datetime.now()
            
            # If we have a recent price (less than 5 minutes old), use it
            if cached_price and (now - datetime.fromisoformat(cached_price['last_updated'])) < timedelta(minutes=5):
                return cached_price['price']
            
            # Otherwise, generate a new price with some random fluctuation
            base_price = PriceService.MOCK_STOCKS[symbol]['base_price']
            fluctuation = random.uniform(-0.02, 0.02)  # ±2%
            new_price = base_price * (1 + fluctuation)
            
            # Cache the new price
            if cached_price:
                cursor.execute(
                    "UPDATE prices SET price = ?, last_updated = ? WHERE symbol = ?",
                    (new_price, now.isoformat(), symbol)
                )
            else:
                cursor.execute(
                    "INSERT INTO prices (symbol, price, last_updated) VALUES (?, ?, ?)",
                    (symbol, new_price, now.isoformat())
                )
            
            return new_price
    
    @staticmethod
    def get_historical_prices(symbol, days=30):
        """Get historical prices for a stock symbol
        
        In a production environment, this would call an external API.
        For simulation, we're generating random historical data.
        
        Args:
            symbol (str): Stock symbol to get prices for
            days (int, optional): Number of days of historical data
            
        Returns:
            list: List of dictionaries with date and price
            
        Raises:
            InvalidSymbolError: If the symbol is not supported
        """
        symbol = symbol.upper()
        
        if symbol not in PriceService.MOCK_STOCKS:
            raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
        
        base_price = PriceService.MOCK_STOCKS[symbol]['base_price']
        current_price = PriceService.get_share_price(symbol)
        
        # Generate historical prices with some randomness but trending toward current price
        historical_data = []
        price = base_price
        
        for i in range(days, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Add some random daily movement
            daily_change = random.uniform(-0.015, 0.015)  # ±1.5%
            
            # Add trend toward current price
            trend_factor = 0.05  # How strongly to trend toward current price
            trend_direction = (current_price - price) / base_price
            trend = trend_direction * trend_factor
            
            # Apply changes
            price = price * (1 + daily_change + trend)
            
            historical_data.append({
                "date": date,
                "price": round(price, 2)
            })
        
        return historical_data
    
    @staticmethod
    def get_stock_info(symbol):
        """Get information about a stock
        
        Args:
            symbol (str): Stock symbol to get info for
            
        Returns:
            dict: Stock information
            
        Raises:
            InvalidSymbolError: If the symbol is not supported
        """
        symbol = symbol.upper()
        
        if symbol not in PriceService.MOCK_STOCKS:
            raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
        
        return {
            "symbol": symbol,
            "name": PriceService.MOCK_STOCKS[symbol]["name"],
            "current_price": PriceService.get_share_price(symbol)
        }
    
    @staticmethod
    def get_available_symbols():
        """Get list of available stock symbols
        
        Returns:
            list: List of available stock symbols
        """
        return list(PriceService.MOCK_STOCKS.keys())
