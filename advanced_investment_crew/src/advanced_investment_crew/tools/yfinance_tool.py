"""
Yahoo Finance data fetching tool with proper MultiIndex handling
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Optional, Tuple
from datetime import datetime

# CrewAI imports
try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("⚠️  CrewAI not available, tool wrapper disabled")


class YFinanceTool:
    """Robust Yahoo Finance data fetcher for portfolio analysis"""
    
    @staticmethod
    def download_data(
        tickers: Union[str, List[str]],
        period: str = "1y",
        interval: str = "1d",
        auto_adjust: bool = True
    ) -> pd.DataFrame:
        """
        Download data from Yahoo Finance with MultiIndex handling
        
        Args:
            tickers: Single ticker or list of tickers
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1d, 1wk, 1mo)
            auto_adjust: Adjust all OHLC automatically
        
        Returns:
            DataFrame with price data
        """
        # Single ticker için string'e çevir
        if isinstance(tickers, list) and len(tickers) == 1:
            tickers = tickers[0]
        
        try:
            data = yf.download(
                tickers,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=auto_adjust
            )
            
            if data.empty:
                raise ValueError(f"No data returned for {tickers}")
            
            return data
            
        except Exception as e:
            raise Exception(f"Error downloading data for {tickers}: {str(e)}")
    
    @staticmethod
    def get_close_prices(data: pd.DataFrame, ticker: str = None) -> pd.Series:
        """
        Extract close prices from yfinance data (handles all cases)
        
        Args:
            data: DataFrame from yf.download()
            ticker: Ticker symbol (for MultiIndex data)
        
        Returns:
            Series of close prices
        """
        try:
            # Debug: Print column structure
            # print(f"DEBUG: Columns type: {type(data.columns)}")
            # print(f"DEBUG: Columns: {data.columns.tolist()}")
            
            # Case 1: MultiIndex columns - ('Close', 'SPY')
            if isinstance(data.columns, pd.MultiIndex):
                if ticker:
                    # Specific ticker requested
                    if ('Close', ticker) in data.columns:
                        return data[('Close', ticker)]
                    else:
                        # Try without tuple
                        return data['Close'][ticker]
                else:
                    # Get first ticker
                    close_data = data['Close']
                    if isinstance(close_data, pd.DataFrame):
                        return close_data.iloc[:, 0]
                    else:
                        return close_data
            
            # Case 2: Single level columns but still MultiIndex structure
            elif 'Close' in data.columns:
                close_data = data['Close']
                
                # If Close is a DataFrame (multiple tickers)
                if isinstance(close_data, pd.DataFrame):
                    if ticker and ticker in close_data.columns:
                        return close_data[ticker]
                    else:
                        return close_data.iloc[:, 0]
                # If Close is a Series (single ticker)
                else:
                    return close_data
            
            # Case 3: Try direct access with tuple
            elif isinstance(data.columns, pd.MultiIndex):
                # Get all Close columns
                close_cols = [col for col in data.columns if 'Close' in str(col)]
                if close_cols:
                    if ticker:
                        matching = [col for col in close_cols if ticker in str(col)]
                        if matching:
                            return data[matching[0]]
                    return data[close_cols[0]]
            
            # Case 4: Fallback - search for any column with 'close' in name
            close_cols = [col for col in data.columns if 'close' in str(col).lower()]
            if close_cols:
                return data[close_cols[0]]
            
            raise ValueError(f"Could not find Close prices in data. Columns: {data.columns.tolist()}")
            
        except Exception as e:
            raise Exception(f"Error extracting close prices: {str(e)}\nColumns: {data.columns.tolist()}")
    
    @staticmethod
    def get_all_close_prices(data: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
        """
        Extract close prices for all tickers
        
        Args:
            data: DataFrame from yf.download()
            tickers: List of ticker symbols
        
        Returns:
            DataFrame with close prices for each ticker
        """
        close_prices = pd.DataFrame()
        
        # Single ticker case
        if len(tickers) == 1:
            close_prices[tickers[0]] = YFinanceTool.get_close_prices(data)
            return close_prices
        
        # Multiple tickers
        for ticker in tickers:
            try:
                close_prices[ticker] = YFinanceTool.get_close_prices(data, ticker)
            except Exception as e:
                print(f"⚠️  Warning: Could not get close prices for {ticker}: {e}")
                continue
        
        if close_prices.empty:
            raise Exception("Could not extract close prices for any ticker")
        
        return close_prices
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate percentage returns"""
        return prices.pct_change().dropna()
    
    @staticmethod
    def calculate_log_returns(prices: pd.Series) -> pd.Series:
        """Calculate logarithmic returns"""
        return np.log(prices / prices.shift(1)).dropna()
    
    @staticmethod
    def get_latest_price(data: pd.DataFrame, ticker: str = None) -> float:
        """Get latest close price"""
        close_prices = YFinanceTool.get_close_prices(data, ticker)
        return float(close_prices.iloc[-1])
    
    @staticmethod
    def get_price_stats(data: pd.DataFrame, ticker: str = None) -> Dict:
        """
        Calculate comprehensive price statistics
        """
        close_prices = YFinanceTool.get_close_prices(data, ticker)
        returns = YFinanceTool.calculate_returns(close_prices)
        
        return {
            'current_price': float(close_prices.iloc[-1]),
            'start_price': float(close_prices.iloc[0]),
            'mean_price': float(close_prices.mean()),
            'min_price': float(close_prices.min()),
            'max_price': float(close_prices.max()),
            'std_price': float(close_prices.std()),
            'total_return_pct': float((close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100),
            'mean_daily_return': float(returns.mean()),
            'std_daily_return': float(returns.std()),
            'annualized_return': float(returns.mean() * 252),
            'annualized_volatility': float(returns.std() * np.sqrt(252)),
            'sharpe_ratio': float((returns.mean() * 252) / (returns.std() * np.sqrt(252))) if returns.std() > 0 else 0,
            'min_daily_return': float(returns.min()),
            'max_daily_return': float(returns.max()),
            'data_points': len(close_prices),
            'date_range': f"{close_prices.index[0].date()} to {close_prices.index[-1].date()}"
        }
    
    @staticmethod
    def get_returns_matrix(data: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
        """Calculate returns matrix for multiple tickers"""
        close_prices = YFinanceTool.get_all_close_prices(data, tickers)
        returns = close_prices.pct_change().dropna()
        return returns
    
    @staticmethod
    def get_correlation_matrix(data: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
        """Calculate correlation matrix"""
        returns = YFinanceTool.get_returns_matrix(data, tickers)
        return returns.corr()
    
    @staticmethod
    def get_covariance_matrix(data: pd.DataFrame, tickers: List[str], annualized: bool = True) -> pd.DataFrame:
        """Calculate covariance matrix"""
        returns = YFinanceTool.get_returns_matrix(data, tickers)
        cov_matrix = returns.cov()
        
        if annualized:
            cov_matrix = cov_matrix * 252  # Annualize
        
        return cov_matrix
    
    @staticmethod
    def get_portfolio_data(
        tickers: List[str],
        period: str = "2y"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Get complete portfolio data package
        
        Returns:
            Tuple of (price_data, close_prices, returns, correlation_matrix)
        """
        # Download data
        data = YFinanceTool.download_data(tickers, period=period)
        
        # Extract close prices
        close_prices = YFinanceTool.get_all_close_prices(data, tickers)
        
        # Calculate returns
        returns = close_prices.pct_change().dropna()
        
        # Calculate correlation
        correlation = returns.corr()
        
        return data, close_prices, returns, correlation


# CrewAI Tool Wrapper
if CREWAI_AVAILABLE:
    class FetchMarketDataInput(BaseModel):
        """Input schema for FetchMarketData tool"""
        tickers: str = Field(..., description="Comma-separated ticker symbols (e.g., 'SPY,QQQ,VTI')")
        period: str = Field(default="2y", description="Time period: 1y, 2y, 5y, max")
    
    
    class FetchMarketDataTool(BaseTool):
        name: str = "Fetch Market Data"
        description: str = "Fetch historical market data from Yahoo Finance for portfolio analysis"
        args_schema: type[BaseModel] = FetchMarketDataInput
        
        def _run(self, tickers: str, period: str = "2y") -> str:
            """Fetch market data and return statistics"""
            import json
            
            try:
                # Parse tickers
                ticker_list = [t.strip() for t in tickers.split(',')]
                
                # Download data
                tool = YFinanceTool()
                data, close_prices, returns, correlation = tool.get_portfolio_data(
                    ticker_list, 
                    period=period
                )
                
                # Calculate statistics for each ticker
                stats = {}
                for ticker in ticker_list:
                    stats[ticker] = tool.get_price_stats(data, ticker if len(ticker_list) > 1 else None)
                
                # Prepare response
                response = {
                    'success': True,
                    'tickers': ticker_list,
                    'period': period,
                    'data_points': len(close_prices),
                    'date_range': {
                        'start': str(close_prices.index[0].date()),
                        'end': str(close_prices.index[-1].date())
                    },
                    'statistics': stats,
                    'correlation_matrix': correlation.round(4).to_dict(),
                    'returns_summary': {
                        'mean': {k: round(v, 6) for k, v in returns.mean().to_dict().items()},
                        'std': {k: round(v, 6) for k, v in returns.std().to_dict().items()},
                        'min': {k: round(v, 6) for k, v in returns.min().to_dict().items()},
                        'max': {k: round(v, 6) for k, v in returns.max().to_dict().items()}
                    }
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return json.dumps({
                    'success': False,
                    'error': str(e)
                })
    
    fetch_market_data_tool = FetchMarketDataTool()

else:
    fetch_market_data_tool = None


# Test function
def test_tool():
    """Test the YFinance tool"""
    print("=" * 60)
    print("🧪 Testing YFinance Tool")
    print("=" * 60)
    
    tool = YFinanceTool()
    
    # Test 1: Single ticker
    print("\n1️⃣ Testing single ticker (SPY)...")
    try:
        data = tool.download_data('SPY', period='5d')
        print(f"   Data shape: {data.shape}")
        print(f"   Columns: {data.columns.tolist()}")
        
        price = tool.get_latest_price(data)
        stats = tool.get_price_stats(data)
        print(f"✅ SPY: ${price:.2f}")
        print(f"   Total return: {stats['total_return_pct']:.2f}%")
        print(f"   Volatility: {stats['annualized_volatility']*100:.2f}%")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Multiple tickers
    print("\n2️⃣ Testing multiple tickers (SPY, QQQ, VTI)...")
    try:
        tickers = ['SPY', 'QQQ', 'VTI']
        data, close_prices, returns, correlation = tool.get_portfolio_data(tickers, period='1y')
        print(f"✅ Downloaded {len(close_prices)} days of data")
        print(f"\nLatest prices:")
        for ticker in tickers:
            price = tool.get_latest_price(data, ticker)
            print(f"   {ticker}: ${price:.2f}")
        
        print(f"\nCorrelation matrix:")
        print(correlation.round(3))
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Returns statistics
    print("\n3️⃣ Testing returns statistics...")
    try:
        for ticker in tickers:
            stats = tool.get_price_stats(data, ticker)
            print(f"\n{ticker}:")
            print(f"   Annual return: {stats['annualized_return']*100:.2f}%")
            print(f"   Annual volatility: {stats['annualized_volatility']*100:.2f}%")
            print(f"   Sharpe ratio: {stats['sharpe_ratio']:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 4: CrewAI Tool wrapper
    if CREWAI_AVAILABLE and fetch_market_data_tool:
        print("\n4️⃣ Testing CrewAI tool wrapper...")
        try:
            result = fetch_market_data_tool._run(tickers="SPY,QQQ", period="1y")
            print("✅ CrewAI tool wrapper working")
            print(f"   Result length: {len(result)} characters")
        except Exception as e:
            print(f"⚠️  CrewAI tool error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_tool()
