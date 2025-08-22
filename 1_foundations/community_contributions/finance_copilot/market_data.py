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
    
    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price and basic info"""
        try:
            # Check cache first
            if self._is_cache_valid(symbol):
                return self.cache[symbol]
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            hist = ticker.history(period="1d")
            if hist.empty:
                return {"error": f"Could not fetch data for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            previous_close = info.get('previousClose', current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            data = {
                "symbol": symbol,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": info.get('volume', 0),
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the data
            self._cache_data(symbol, data)
            return data
            
        except Exception as e:
            return {"error": f"Error fetching data for {symbol}: {str(e)}"}
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """Get current cryptocurrency price"""
        try:
            # Check cache first
            if self._is_cache_valid(symbol):
                return self.cache[symbol]
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                return {"error": f"Could not fetch data for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Open'].iloc[0]
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            data = {
                "symbol": symbol,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": hist['Volume'].iloc[-1],
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the data
            self._cache_data(symbol, data)
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
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_expiry.clear()
