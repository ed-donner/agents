#!/usr/bin/env python3
"""
Robust Yahoo Finance test with utility function
"""

import yfinance as yf
import pandas as pd

def get_close_price(data, ticker=None):
    """
    Safely extract close price from yfinance data
    Handles both MultiIndex and regular Index
    
    Args:
        data: DataFrame from yf.download()
        ticker: Ticker symbol (optional, for MultiIndex)
    
    Returns:
        float: Latest close price
    """
    try:
        # Check if MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            # MultiIndex: ('Close', 'SPY')
            if ticker:
                return float(data[('Close', ticker)].iloc[-1])
            else:
                # Get first ticker
                return float(data['Close'].iloc[-1, 0])
        else:
            # Regular Index: 'Close'
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"Error extracting close price: {e}")
        # Fallback: try different methods
        try:
            return float(data['Close'].values[-1])
        except:
            return float(data.iloc[-1]['Close'])


def test_yfinance():
    """Test yfinance with proper error handling"""
    print("Testing yfinance...")
    print("=" * 60)
    
    try:
        ticker = 'SPY'
        print(f"Downloading {ticker} data...")
        
        # Method 1: Single ticker without group_by
        data = yf.download(
            ticker,
            period='5d',
            progress=False,
            auto_adjust=True
        )
        
        if data.empty:
            print("❌ No data returned")
            return False
        
        print(f"✅ Data downloaded successfully")
        print(f"   Shape: {data.shape}")
        print(f"   Columns: {data.columns.tolist()}")
        
        # Extract close price safely
        close_price = get_close_price(data, ticker)
        
        print(f"\n📊 Results:")
        print(f"   Latest close: ${close_price:.2f}")
        print(f"   Data points: {len(data)} days")
        print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
        
        # Show last few rows
        print(f"\n📈 Last 3 trading days:")
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten MultiIndex for display
            display_data = data.copy()
            display_data.columns = [col[0] for col in data.columns]
            print(display_data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
        else:
            print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_yfinance()
    exit(0 if success else 1)

