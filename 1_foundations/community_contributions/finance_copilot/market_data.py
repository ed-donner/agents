import yfinance as yf
import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time
from config import Config

class MarketDataTool:
    def __init__(self):
        self.config = Config()
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
        
        # Common cryptocurrency symbol mappings
        self.crypto_symbols = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'USDT': 'USDT-USD',
            'BNB': 'BNB-USD',
            'SOL': 'SOL-USD',
            'ADA': 'ADA-USD',
            'XRP': 'XRP-USD',
            'DOT': 'DOT-USD',
            'DOGE': 'DOGE-USD',
            'AVAX': 'AVAX-USD',
            'LINK': 'LINK-USD',
            'LTC': 'LTC-USD',
            'BCH': 'BCH-USD',
            'UNI': 'UNI-USD',
            'ATOM': 'ATOM-USD',
            'FIL': 'FIL-USD',
            'NEAR': 'NEAR-USD',
            'ALGO': 'ALGO-USD',
            'VET': 'VET-USD',
            'ICP': 'ICP-USD'
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_expiry.clear()
        print("🧹 Cache cleared")
    
    def _resolve_crypto_symbol(self, symbol: str) -> str:
        """Resolve common crypto symbols to their correct Yahoo Finance format"""
        clean_symbol = symbol.strip().upper()
        
        # Check if it's a known crypto symbol
        if clean_symbol in self.crypto_symbols:
            resolved_symbol = self.crypto_symbols[clean_symbol]
            print(f"🔍 Resolved {clean_symbol} → {resolved_symbol}")
            return resolved_symbol
        
        # If it already has -USD suffix, return as is
        if clean_symbol.endswith('-USD'):
            return clean_symbol
        
        # If it's a 3-4 letter symbol that might be crypto, add -USD
        if len(clean_symbol) <= 4 and clean_symbol.isalpha():
            # Check if it's actually a cryptocurrency
            try:
                test_ticker = yf.Ticker(clean_symbol)
                if test_ticker.info.get('quoteType') == 'CRYPTOCURRENCY':
                    return clean_symbol  # Already correct format
                elif test_ticker.info.get('quoteType') == 'ETF' or test_ticker.info.get('quoteType') == 'EQUITY':
                    # This is a stock/ETF, not crypto - add -USD to get crypto version
                    crypto_symbol = f"{clean_symbol}-USD"
                    print(f"⚠️  {clean_symbol} is a stock/ETF, trying crypto version: {crypto_symbol}")
                    return crypto_symbol
            except:
                pass
        
        return clean_symbol
    
    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price and basic info"""
        try:
            # Check cache first
            if self._is_cache_valid(symbol):
                return self.cache[symbol]
            
            # Clean the symbol (remove any extra characters)
            clean_symbol = symbol.strip().upper()
            
            ticker = yf.Ticker(clean_symbol)
            
            # Try to get basic info first
            try:
                info = ticker.info
                if not info or 'regularMarketPrice' not in info:
                    return {"error": f"Could not fetch basic info for {clean_symbol}"}
            except Exception as e:
                return {"error": f"Error fetching info for {clean_symbol}: {str(e)}"}
            
            # Get current price from info (more reliable than history)
            current_price = info.get('regularMarketPrice', 0)
            if not current_price:
                # Fallback to history method
                try:
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        return {"error": f"No price data available for {clean_symbol}"}
                except Exception as e:
                    return {"error": f"Error fetching historical data for {clean_symbol}: {str(e)}"}
            
            # Get previous close
            previous_close = info.get('previousClose', current_price)
            if not previous_close:
                previous_close = current_price
            
            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            data = {
                "symbol": clean_symbol,
                "price": round(float(current_price), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": int(info.get('volume', 0)) if info.get('volume') else 0,
                "market_cap": int(info.get('marketCap', 0)) if info.get('marketCap') else 0,
                "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0,
                "dividend_yield": float(info.get('dividendYield', 0)) if info.get('dividendYield') else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the data
            self._cache_data(clean_symbol, data)
            return data
            
        except Exception as e:
            return {"error": f"Error fetching data for {symbol}: {str(e)}"}
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """Get current cryptocurrency price"""
        try:
            # Resolve the symbol to get the correct crypto ticker
            resolved_symbol = self._resolve_crypto_symbol(symbol)
            
            # Check cache first
            if self._is_cache_valid(resolved_symbol):
                return self.cache[resolved_symbol]
            
            ticker = yf.Ticker(resolved_symbol)
            
            # Try to get basic info first (more reliable than history)
            try:
                info = ticker.info
                if not info:
                    return {"error": f"Could not fetch basic info for {resolved_symbol}"}
            except Exception as e:
                return {"error": f"Error fetching info for {resolved_symbol}: {str(e)}"}
            
            # Verify this is actually a cryptocurrency
            quote_type = info.get('quoteType', '')
            if quote_type != 'CRYPTOCURRENCY':
                return {"error": f"{resolved_symbol} is not a cryptocurrency (type: {quote_type}). Try using the full symbol like 'BTC-USD'."}
            
            # Get current price from info (more reliable than history)
            current_price = info.get('regularMarketPrice', 0)
            if not current_price:
                # Fallback to history method
                try:
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        return {"error": f"No price data available for {resolved_symbol}"}
                except Exception as e:
                    return {"error": f"Error fetching historical data for {resolved_symbol}: {str(e)}"}
            
            # Get previous close
            previous_close = info.get('previousClose', current_price)
            if not previous_close:
                previous_close = current_price
            
            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            # Convert numpy/pandas types to native Python types for JSON serialization
            volume = int(info.get('volume', 0)) if info.get('volume') else 0
            
            data = {
                "symbol": resolved_symbol,
                "original_symbol": symbol,  # Keep track of what user originally asked for
                "price": round(float(current_price), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": volume,
                "market_cap": int(info.get('marketCap', 0)) if info.get('marketCap') else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the data
            self._cache_data(resolved_symbol, data)
            return data
            
        except Exception as e:
            return {"error": f"Error fetching data for {symbol}: {str(e)}"}
    
    def get_stock_fundamentals(self, symbol: str) -> Dict:
        """Get detailed stock fundamentals"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get financial statements
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt
            cash_flow = ticker.cashflow
            
            fundamentals = {
                "symbol": symbol,
                "company_name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "market_cap": info.get('marketCap', 0),
                "enterprise_value": info.get('enterpriseValue', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "forward_pe": info.get('forwardPE', 0),
                "peg_ratio": info.get('pegRatio', 0),
                "price_to_book": info.get('priceToBook', 0),
                "price_to_sales": info.get('priceToSalesTrailing12Months', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "payout_ratio": info.get('payoutRatio', 0),
                "debt_to_equity": info.get('debtToEquity', 0),
                "current_ratio": info.get('currentRatio', 0),
                "quick_ratio": info.get('quickRatio', 0),
                "return_on_equity": info.get('returnOnEquity', 0),
                "return_on_assets": info.get('returnOnAssets', 0),
                "profit_margins": info.get('profitMargins', 0),
                "operating_margins": info.get('operatingMargins', 0),
                "ebitda_margins": info.get('ebitdaMargins', 0),
                "revenue_growth": info.get('revenueGrowth', 0),
                "earnings_growth": info.get('earningsGrowth', 0),
                "timestamp": datetime.now().isoformat()
            }
            
            return fundamentals
            
        except Exception as e:
            return {"error": f"Error fetching fundamentals for {symbol}: {str(e)}"}
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            return pd.DataFrame()
    
    def get_company_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get company news using Alpha Vantage API"""
        if not self.config.ALPHA_VANTAGE_API_KEY:
            return []
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.config.ALPHA_VANTAGE_API_KEY,
                "limit": limit
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "feed" in data:
                news = []
                for item in data["feed"]:
                    news.append({
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", ""),
                        "published": item.get("time_published", ""),
                        "source": item.get("source", "Unknown source"),  # Extract source field
                        "authors": item.get("authors", []),  # Extract authors
                        "category": item.get("category_within_source", ""),  # Extract category
                        "source_domain": item.get("source_domain", ""),  # Extract source domain
                        "sentiment": item.get("overall_sentiment_label", ""),
                        "sentiment_score": item.get("overall_sentiment_score", 0)
                    })
                return news
            else:
                return []
                
        except Exception as e:
            return []
    
    def get_market_summary(self) -> Dict:
        """Get market summary for major indices"""
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow, NASDAQ, Russell 2000
        
        summary = {}
        for index in indices:
            try:
                data = self.get_stock_price(index)
                if "error" not in data:
                    summary[index] = data
            except:
                continue
        
        return summary
    
    def get_portfolio_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current prices for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            if symbol.endswith('-USD'):
                results[symbol] = self.get_crypto_price(symbol)
            else:
                results[symbol] = self.get_stock_price(symbol)
            
            # Rate limiting to avoid API issues
            time.sleep(0.1)
        
        return results
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache or symbol not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[symbol]
    
    def _cache_data(self, symbol: str, data: Dict):
        """Cache data with expiry"""
        self.cache[symbol] = data
        self.cache_expiry[symbol] = datetime.now() + timedelta(seconds=self.cache_duration)
