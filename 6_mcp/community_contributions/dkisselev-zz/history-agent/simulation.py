from datetime import datetime, timedelta
from typing import Optional
from polygon import RESTClient
from dotenv import load_dotenv
import os
import time
import random
from database import read_market, write_market, set_simulation_date

load_dotenv(override=True)

# Global cache for historical data
_historical_cache: Optional['HistoricalDataCache'] = None

def get_historical_price(date_str: str, symbol: str, allow_api_fetch: bool = False) -> Optional[float]:
    """
    Get historical price for a symbol on a specific date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        symbol: Stock symbol
        allow_api_fetch: If True and not in DB, fetch from API
    
    Returns:
        float: Price if found
        None: If not found and API fetch not allowed/failed
    """
    # Check database first
    market_data = read_market(date_str)
    if market_data and symbol in market_data:
        return market_data[symbol]
    
    # Try API fetch
    if allow_api_fetch:
        cache = get_historical_cache()
        if cache and cache.client:
            return cache._fetch_from_api(date_str, symbol)
    
    return None


def init_simulation_cache(cache: Optional['HistoricalDataCache']):
    """Initialize historical data cache for the trading floor process"""
    global _historical_cache
    _historical_cache = cache


def get_historical_cache() -> Optional['HistoricalDataCache']:
    """Get historical data cache (None if in live mode or different process)"""
    return _historical_cache


class SimulationClock:
    """
    Manages virtual time during simulation.
    """
    
    # US Market Holidays (market holidays)
    MARKET_HOLIDAYS = [
        (1, 1),   # New Year's Day
        (6, 19),  # Juneteenth
        (7, 4),   # Independence Day
        (12, 25), # Christmas
    ]
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        self.current_date = self.start_date
        
        while not self._is_trading_day(self.current_date):
            self.current_date += timedelta(days=1)
        
        set_simulation_date(self.get_current_date())
    
    def _is_trading_day(self, date) -> bool:
        """Check if date is a trading day (not weekend or holiday)"""

        if date.weekday() >= 5:
            return False
        
        if (date.month, date.day) in self.MARKET_HOLIDAYS:
            return False
        
        return True
        
    def advance(self):
        """
        Move to next trading day
        """
        self.current_date += timedelta(days=1)
        
        while not self._is_trading_day(self.current_date):
            self.current_date += timedelta(days=1)
        
        set_simulation_date(self.get_current_date())
    
    def is_complete(self) -> bool:
        """Check if simulation has finished"""
        return self.current_date > self.end_date
    
    def get_current_date(self) -> str:
        """Return current simulated date as string"""
        return self.current_date.strftime("%Y-%m-%d")
    
    def get_current_datetime(self) -> str:
        """Return current simulated datetime for logging"""
        return self.current_date.strftime("%Y-%m-%d 16:00:00")
    
    def get_trading_days_count(self) -> int:
        """Calculate approximate number of trading days in range"""
        total_days = (self.end_date - self.start_date).days
        # Rough estimate: 5/7 of days are trading days
        return int(total_days * 5 / 7)


class HistoricalDataCache:
    """Cache historical prices on-demand to minimize API calls"""
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        self.cache = {}  # Format: {(date_str, symbol): price}
        self.api_key = os.getenv("MASSIVE_API_KEY")
        self.client = RESTClient(self.api_key) if self.api_key else None
        self.api_calls_made = 0
        self.cache_hits = 0
    
    def get_price_for_symbol(self, date_str: str, symbol: str) -> float:
        """
        Get price for a specific symbol on a specific date.
        """
        # Check in-memory cache
        cache_key = (date_str, symbol)
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        price = get_historical_price(date_str, symbol, allow_api_fetch=True)
        
        if price is not None:
            self.cache[cache_key] = price
            self.cache_hits += 1
            return price
        
        # Fallback for missing data 
        price = float(random.randint(50, 200))
        self.cache[cache_key] = price
        return price
    
    def _fetch_from_api(self, date_str: str, symbol: str) -> Optional[float]:
        """
        Fetch price from API and persist to database.
        """
        if not self.client:
            return None
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Fetch daily OHLC data for this specific date
            result = self.client.get_daily_open_close_agg(symbol, date_obj, adjusted=True)
            
            if result and hasattr(result, 'close'):
                price = result.close
                self.api_calls_made += 1
                
                # Persist to database
                existing_data = read_market(date_str) or {}
                existing_data[symbol] = price
                write_market(date_str, existing_data)
                
                print(f"API Call #{self.api_calls_made}: Fetched {symbol} for {date_str} = ${price:.2f} (saved to DB)")
                
                # Rate limiting: Free tier = 5 calls/min
                if self.api_calls_made < 1000:
                    print("Rate limit pause (15s)...")
                    time.sleep(15)
                
                return price
            else:
                print(f"{symbol} not found for {date_str}")
                return None
                
        except Exception as e:
            print(f"Error fetching {symbol} for {date_str}: {e}")
            return None
    
    def get_statistics(self) -> dict:
        """Return cache statistics"""
        return {
            'cache_entries': len(self.cache),
            'api_calls': self.api_calls_made,
            'cache_hits': self.cache_hits,
            'hit_rate': f"{(self.cache_hits / (self.cache_hits + self.api_calls_made) * 100):.1f}%" if (self.cache_hits + self.api_calls_made) > 0 else "N/A"
        }

