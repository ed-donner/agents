#!/usr/bin/env python3
"""
Test script to verify portfolio charts are working correctly
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_portfolio_charts():
    """Test portfolio chart generation"""
    try:
        print("🧪 Testing portfolio chart generation...")
        
        # Import required modules
        from config import Config
        from database import FinanceDatabase
        from market_data import MarketDataTool
        from analysis_tool import AnalysisTool
        
        # Initialize components
        config = Config()
        db = FinanceDatabase(config.DATABASE_PATH)
        market_data = MarketDataTool()
        analysis_tool = AnalysisTool()
        
        print("✅ Components initialized")
        
        # Add sample portfolio data if empty
        portfolio = db.get_portfolio()
        if portfolio.empty:
            print("📝 Adding sample portfolio data...")
            db.add_portfolio_item("AAPL", 100, 150.00)
            db.add_portfolio_item("GOOGL", 50, 2800.00)
            db.add_portfolio_item("TSLA", 25, 800.00)
            print("✅ Sample data added")
        
        # Get portfolio data
        portfolio = db.get_portfolio()
        if portfolio.empty:
            print("❌ Portfolio is still empty")
            return False
        
        print(f"📊 Portfolio has {len(portfolio)} holdings")
        
        # Convert to dict format
        portfolio_dict = {}
        for _, row in portfolio.iterrows():
            portfolio_dict[row['symbol']] = {
                'shares': row['shares'],
                'avg_price': row['avg_price']
            }
        
        # Get current prices
        symbols = list(portfolio_dict.keys())
        print(f"🔍 Fetching prices for: {symbols}")
        
        current_prices = market_data.get_portfolio_prices(symbols)
        print("✅ Current prices fetched")
        
        # Test chart creation
        print("📈 Testing chart creation...")
        
        # Test analysis tool charts
        charts = analysis_tool.create_portfolio_charts(portfolio_dict, current_prices)
        
        if "error" not in charts:
            print("✅ Analysis tool charts created successfully")
            print(f"   - Total value: ${charts['total_value']:,.2f}")
            print(f"   - Number of symbols: {len(charts['symbols'])}")
        else:
            print(f"❌ Analysis tool charts error: {charts['error']}")
        
        # Test portfolio metrics
        metrics = analysis_tool.calculate_portfolio_metrics(portfolio_dict, current_prices)
        
        if "error" not in metrics:
            print("✅ Portfolio metrics calculated successfully")
            print(f"   - Total value: ${metrics['total_value']:,.2f}")
            print(f"   - Total P&L: ${metrics['total_pnl']:+,.2f}")
        else:
            print(f"❌ Portfolio metrics error: {metrics['error']}")
        
        print("\n🎉 Portfolio chart tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_portfolio_charts()
    if success:
        print("\n✅ Charts are working! You can now run the main app.")
        print("   Run: python app.py")
    else:
        print("\n❌ Fix the chart issues before running the main app")
