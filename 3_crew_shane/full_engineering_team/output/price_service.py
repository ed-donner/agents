import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from output.database import Database

logger = logging.getLogger(__name__)

class PriceService:
    """Stock price service for the trading simulation platform."""
    
    def __init__(self, database: Database, use_random: bool = False):
        """Initialize the price service.
        
        Args:
            database (Database): Database manager instance
            use_random (bool): Whether to use random prices for simulation
        """
        self.db = database
        self.use_random = use_random
        self.price_cache = {}
        self.price_cache_expiry = {}
        self.cache_duration = timedelta(minutes=15)  # Cache prices for 15 minutes
        
        # Sample stock data for simulation
        self.sample_stocks = {
            "AAPL": {"base_price": 150.0, "volatility": 0.02},
            "GOOGL": {"base_price": 2800.0, "volatility": 0.025},
            "MSFT": {"base_price": 300.0, "volatility": 0.018},
            "AMZN": {"base_price": 3300.0, "volatility": 0.03},
            "META": {"base_price": 330.0, "volatility": 0.028},
            "TSLA": {"base_price": 700.0, "volatility": 0.04},
            "NFLX": {"base_price": 500.0, "volatility": 0.035},
            "NVDA": {"base_price": 220.0, "volatility": 0.03},
            "JPM": {"base_price": 150.0, "volatility": 0.015},
            "V": {"base_price": 220.0, "volatility": 0.012},
        }
    
    def _get_random_price(self, symbol: str) -> Optional[float]:
        """Generate a random price for a stock symbol based on its base price and volatility.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Optional[float]: Random price if symbol exists, None otherwise
        """
        if symbol not in self.sample_stocks:
            return None
        
        stock_data = self.sample_stocks[symbol]
        base_price = stock_data["base_price"]
        volatility = stock_data["volatility"]
        
        # Generate random price within volatility range
        price_change = random.uniform(-volatility, volatility) * base_price
        price = base_price + price_change
        
        # Ensure price is positive
        return max(0.01, round(price, 2))
    
    def _get_price_from_db(self, symbol: str) -> Optional[float]:
        """Get the most recent price for a symbol from the database.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Optional[float]: Price if found, None otherwise
        """
        try:
            prices = self.db.execute_query(
                "SELECT price FROM prices WHERE symbol = ?",
                (symbol,)
            )
            
            if not prices:
                return None
            
            return prices[0]['price']
            
        except Exception as e:
            logger.error(f"Error retrieving price from database: {e}")
            return None
    
    def _update_price_in_db(self, symbol: str, price: float) -> bool:
        """Update or insert a price in the database.
        
        Args:
            symbol (str): Stock symbol
            price (float): Current price
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Check if price exists for this symbol
            existing_price = self._get_price_from_db(symbol)
            
            if existing_price is not None:
                # Update existing price
                self.db.execute_update(
                    "UPDATE prices SET price = ?, timestamp = ? WHERE symbol = ?",
                    (price, datetime.now().isoformat(), symbol)
                )
            else:
                # Insert new price
                self.db.execute_insert(
                    "INSERT INTO prices (symbol, price) VALUES (?, ?)",
                    (symbol, price)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating price in database: {e}")
            return False
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get the current price for a stock symbol.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Optional[float]: Current price if available, None otherwise
        """
        try:
            # Check if price is in cache and not expired
            now = datetime.now()
            if symbol in self.price_cache and self.price_cache_expiry[symbol] > now:
                return self.price_cache[symbol]
            
            # Generate or fetch price
            if self.use_random:
                # Use random price for simulation
                price = self._get_random_price(symbol)
            else:
                # In a real implementation, this would fetch from an external API
                # For now, we'll use the database or fall back to random
                price = self._get_price_from_db(symbol) or self._get_random_price(symbol)
            
            if price is None:
                logger.error(f"Unable to get price for symbol: {symbol}")
                return None
            
            # Update cache
            self.price_cache[symbol] = price
            self.price_cache_expiry[symbol] = now + self.cache_duration
            
            # Update database
            self._update_price_in_db(symbol, price)
            
            return price
            
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    def get_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple stock symbols.
        
        Args:
            symbols (List[str]): List of stock symbols
            
        Returns:
            Dict[str, Optional[float]]: Dictionary mapping symbols to prices
        """
        return {symbol: self.get_price(symbol) for symbol in symbols}
    
    def get_available_symbols(self) -> List[str]:
        """Get a list of available stock symbols.
        
        Returns:
            List[str]: List of available symbols
        """
        return list(self.sample_stocks.keys())
