"""
Market Data Fetcher Module
Handles data retrieval from Yahoo Finance for different markets
"""

import yfinance as yf
import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetch and manage market data for different markets (Global, Turkey)
    
    Attributes:
        market_type (str): Type of market ('global' or 'turkey')
        config (dict): Market configuration
        metadata (dict): Ticker metadata
    """
    
    def __init__(self, market_type: str = 'global'):
        """
        Initialize data fetcher
        
        Args:
            market_type: 'global' or 'turkey'
            
        Raises:
            ValueError: If market_type is invalid
            FileNotFoundError: If config files are missing
        """
        if market_type not in ['global', 'turkey']:
            raise ValueError(f"Invalid market_type: {market_type}. Must be 'global' or 'turkey'")
        
        self.market_type = market_type
        self.config = self._load_config()
        self.metadata = self._load_metadata()
        
        logger.info(f"Initialized MarketDataFetcher for {market_type} market")
        
    def _load_config(self) -> Dict:
        """
        Load market configuration from YAML file
        
        Returns:
            Dictionary with market configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path('config/market_config.yaml')
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                "Please ensure config/market_config.yaml exists"
            )
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            if 'markets' not in full_config:
                raise ValueError("Invalid config file: 'markets' key not found")
            
            if self.market_type not in full_config['markets']:
                raise ValueError(f"Market '{self.market_type}' not found in config")
            
            return full_config['markets'][self.market_type]
            
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise
    
    def _load_metadata(self) -> Dict:
        """
        Load ticker metadata from JSON file
        
        Returns:
            Dictionary with ticker metadata
        """
        metadata_path = Path('config/ticker_metadata.json')
        
        if not metadata_path.exists():
            logger.warning(f"Metadata file not found: {metadata_path}")
            return {}
            
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {}
    
    def get_tickers(self) -> List[str]:
        """
        Get list of tickers for current market
        
        Returns:
            List of ticker symbols
        """
        return self.config['tickers']
    
    def get_currency(self) -> str:
        """
        Get currency for current market
        
        Returns:
            Currency code (e.g., 'USD', 'TRY')
        """
        return self.config['currency']
    
    def get_risk_free_rate(self) -> float:
        """
        Get risk-free rate for current market
        
        Returns:
            Annual risk-free rate as decimal
        """
        return self.config['risk_free_rate']
    
    def get_market_name(self) -> str:
        """
        Get display name for current market
        
        Returns:
            Market display name
        """
        return self.config.get('market_name', self.market_type.title())
    
    def get_ticker_info(self, ticker: str) -> Dict:
        """
        Get metadata for a specific ticker
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Dictionary with ticker information
        """
        default_info = {
            'name': ticker,
            'sector': 'Unknown',
            'description': 'No description available',
            'expense_ratio': None,
            'aum': None
        }
        
        return self.metadata.get(ticker, default_info)
    
    def fetch_data(self, 
                   tickers: Optional[List[str]] = None,
                   period: str = '2y',
                   interval: str = '1d') -> pd.DataFrame:
        """
        Fetch historical price data from Yahoo Finance
        
        Args:
            tickers: List of ticker symbols (uses default if None)
            period: Data period (e.g., '1y', '2y', '5y', 'max')
            interval: Data interval (e.g., '1d', '1wk', '1mo')
            
        Returns:
            DataFrame with multi-level columns (ticker, price_type)
            
        Raises:
            ValueError: If no data is retrieved
        """
        if tickers is None:
            tickers = self.get_tickers()
        
        logger.info(f"Fetching data for {len(tickers)} tickers: {tickers}")
        logger.info(f"Period: {period}, Interval: {interval}")
        
        try:
            # Download data from Yahoo Finance
            data = yf.download(
                tickers,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                group_by='ticker',
                threads=True
            )
            
            if data.empty:
                raise ValueError("No data retrieved from Yahoo Finance")
            
            # Handle single vs multiple tickers
            if len(tickers) == 1:
                # Single ticker - restructure to match multi-ticker format
                ticker = tickers[0]
                data.columns = pd.MultiIndex.from_product(
                    [[ticker], data.columns],
                    names=['Ticker', 'Price']
                )
            
            # Remove any rows with all NaN values
            data = data.dropna(how='all')
            
            logger.info(f"Successfully fetched data: {data.shape[0]} rows, {len(tickers)} tickers")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise
    
    def get_close_prices(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract close prices from multi-level DataFrame
        
        Args:
            data: Multi-level DataFrame from fetch_data()
            
        Returns:
            DataFrame with close prices only (tickers as columns)
            
        Raises:
            ValueError: If close prices cannot be extracted
        """
        try:
            # Get all tickers from the first level of columns
            if isinstance(data.columns, pd.MultiIndex):
                tickers = data.columns.get_level_values(0).unique()
            else:
                # Single ticker case
                return data[['Close']].rename(columns={'Close': data.columns[0]})
            
            # Extract close prices for each ticker
            close_prices = pd.DataFrame()
            
            for ticker in tickers:
                try:
                    if 'Close' in data[ticker].columns:
                        close_prices[ticker] = data[ticker]['Close']
                    else:
                        logger.warning(f"No 'Close' column found for {ticker}")
                except Exception as e:
                    logger.warning(f"Error extracting close price for {ticker}: {str(e)}")
            
            if close_prices.empty:
                raise ValueError("No close prices could be extracted")
            
            # Drop rows with any NaN values
            close_prices = close_prices.dropna()
            
            logger.info(f"Extracted close prices: {close_prices.shape}")
            
            return close_prices
            
        except Exception as e:
            logger.error(f"Error extracting close prices: {str(e)}")
            raise
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily returns from prices
        
        Args:
            prices: DataFrame with price data
            
        Returns:
            DataFrame with daily returns
        """
        returns = prices.pct_change().dropna()
        logger.info(f"Calculated returns: {returns.shape}")
        return returns
    
    def get_summary_statistics(self, prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate summary statistics for tickers
        
        Args:
            prices: DataFrame with price data
            returns: DataFrame with return data
            
        Returns:
            DataFrame with statistics for each ticker
        """
        stats = []
        
        for ticker in prices.columns:
            total_return = (prices[ticker].iloc[-1] / prices[ticker].iloc[0] - 1) * 100
            annual_return = returns[ticker].mean() * 252 * 100
            annual_vol = returns[ticker].std() * np.sqrt(252) * 100
            sharpe = (annual_return/100 - self.get_risk_free_rate()) / (annual_vol/100)
            
            info = self.get_ticker_info(ticker)
            
            stats.append({
                'Ticker': ticker,
                'Name': info['name'],
                'Sector': info['sector'],
                'Latest Price': f"{prices[ticker].iloc[-1]:.2f}",
                'Total Return': f"{total_return:.2f}%",
                'Annual Return': f"{annual_return:.2f}%",
                'Annual Volatility': f"{annual_vol:.2f}%",
                'Sharpe Ratio': f"{sharpe:.2f}"
            })
        
        return pd.DataFrame(stats)
    
    def validate_data(self, data: pd.DataFrame, min_days: int = 252) -> Tuple[bool, str]:
        """
        Validate fetched data
        
        Args:
            data: DataFrame to validate
            min_days: Minimum required days of data
            
        Returns:
            Tuple of (is_valid, message)
        """
        if data.empty:
            return False, "Data is empty"
        
        if len(data) < min_days:
            return False, f"Insufficient data: {len(data)} days (minimum {min_days} required)"
        
        # Check for excessive missing data
        missing_pct = data.isnull().sum().sum() / (data.shape[0] * data.shape[1]) * 100
        if missing_pct > 10:
            return False, f"Too much missing data: {missing_pct:.1f}%"
        
        return True, "Data validation passed"
