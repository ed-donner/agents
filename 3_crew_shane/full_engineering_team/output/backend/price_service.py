import logging
import random
import time
from datetime import datetime, timedelta
from .database import db

class PriceService:
    def __init__(self):
        """Initialize price service module."""
        self.logger = logging.getLogger(__name__)
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)
    
    def get_current_price(self, symbol):
        """Get the current price for a stock symbol.
        
        In a real implementation, this would call an external API.
        For simulation purposes, we're either returning cached data or generating random prices.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float: Current stock price
        """
        try:
            # Check cache first
            cached_price = self._get_cached_price(symbol)
            if cached_price is not None:
                return cached_price
            
            # In a real implementation, this would call an external API
            # For simulation, generate a random price between $1 and $1000
            price = self._fetch_price_from_external_api(symbol)
            
            # Cache the price
            self._cache_price(symbol, price)
            
            return price
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_historical_prices(self, symbol, days=30):
        """Get historical prices for a stock symbol.
        
        In a real implementation, this would call an external API.
        For simulation purposes, we're generating random historical data.
        
        Args:
            symbol (str): Stock symbol
            days (int, optional): Number of days of historical data to return
            
        Returns:
            list: List of dictionaries with date and price
        """
        try:
            # In a real implementation, this would call an external API
            # For simulation, generate random historical prices
            current_price = self.get_current_price(symbol)
            if current_price is None:
                return []
            
            historical_prices = []
            for day in range(days, 0, -1):
                date = datetime.now() - timedelta(days=day)
                # Generate price with some random variation around the current price
                # This creates somewhat realistic price movements
                variation = random.uniform(-0.05, 0.05)  # +/- 5%
                price = current_price * (1 + variation * (days - day) / days)
                
                historical_prices.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': round(price, 2)
                })
            
            return historical_prices
        except Exception as e:
            self.logger.error(f"Error getting historical prices for {symbol}: {e}")
            return []
    
    def _get_cached_price(self, symbol):
        """Get a cached price if it exists and is not expired.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float: Cached price if valid, None otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT price, updated_at 
                       FROM prices 
                       WHERE symbol = ?""",
                    (symbol,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                # Check if cache is expired
                updated_at = datetime.strptime(result['updated_at'], '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - updated_at).total_seconds() > self.cache_duration:
                    return None
                
                return float(result['price'])
        except Exception as e:
            self.logger.error(f"Error getting cached price: {e}")
            return None
    
    def _cache_price(self, symbol, price):
        """Cache a price for a stock symbol.
        
        Args:
            symbol (str): Stock symbol
            price (float): Stock price
            
        Returns:
            bool: True if cache successful, False otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO prices (symbol, price) 
                       VALUES (?, ?) 
                       ON CONFLICT(symbol) 
                       DO UPDATE SET price = ?, updated_at = CURRENT_TIMESTAMP""",
                    (symbol, price, price)
                )
                return True
        except Exception as e:
            self.logger.error(f"Error caching price: {e}")
            return False
    
    def _fetch_price_from_external_api(self, symbol):
        """Simulate fetching price from an external API.
        
        In a real implementation, this would call an actual stock price API.
        For simulation purposes, we're generating random prices with some base values for common stocks.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float: Simulated stock price
        """
        # Simulate network latency
        time.sleep(0.1)
        
        # Base prices for some common stocks
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'GOOGL': 2800.0,
            'AMZN': 3300.0,
            'META': 330.0,
            'TSLA': 750.0,
            'NFLX': 550.0,
            'NVDA': 200.0
        }
        
        # Get base price or generate a random one
        base = base_prices.get(symbol.upper(), random.uniform(10, 500))
        
        # Add some random variation (+/- 2%)
        variation = random.uniform(-0.02, 0.02)
        price = base * (1 + variation)
        
        return round(price, 2)

# Create a singleton instance
price_service = PriceService()
