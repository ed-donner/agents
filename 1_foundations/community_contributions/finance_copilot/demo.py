#!/usr/bin/env python3
"""
Finance Copilot Demo Script
Demonstrates the key features and capabilities of the Finance Copilot system.
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import FinanceDatabase
from market_data import MarketDataTool
from analysis_tool import AnalysisTool
from notification_system import NotificationSystem
from ai_agent import FinanceCopilotAgent

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_market_data():
    """Demonstrate market data capabilities"""
    print_section("Market Data Demo")
    
    market_data = MarketDataTool()
    
    # Test stock data
    print("📈 Getting stock data for AAPL...")
    try:
        stock_data = market_data.get_stock_price("AAPL")
        if "error" not in stock_data:
            print(f"✅ AAPL: ${stock_data['price']:.2f} ({stock_data['change_percent']:+.2f}%)")
        else:
            print(f"❌ Error: {stock_data['error']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test crypto data
    print("\n🪙 Getting crypto data for BTC-USD...")
    try:
        crypto_data = market_data.get_crypto_price("BTC-USD")
        if "error" not in crypto_data:
            print(f"✅ BTC: ${crypto_data['price']:,.2f} ({crypto_data['change_percent']:+.2f}%)")
        else:
            print(f"❌ Error: {crypto_data['error']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test market summary
    print("\n📊 Getting market summary...")
    try:
        market_summary = market_data.get_market_summary()
        for index, data in market_summary.items():
            if "error" not in data:
                index_name = {
                    '^GSPC': 'S&P 500',
                    '^DJI': 'Dow Jones',
                    '^IXIC': 'NASDAQ',
                    '^RUT': 'Russell 2000'
                }.get(index, index)
                print(f"✅ {index_name}: {data['change_percent']:+.2f}%")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def demo_portfolio_management():
    """Demonstrate portfolio management capabilities"""
    print_section("Portfolio Management Demo")
    
    db = FinanceDatabase(Config().DATABASE_PATH)
    
    # Add some sample portfolio items
    print("➕ Adding sample portfolio items...")
    try:
        db.add_portfolio_item("AAPL", 100, 150.00)
        db.add_portfolio_item("GOOGL", 50, 2800.00)
        db.add_portfolio_item("TSLA", 25, 800.00)
        print("✅ Sample portfolio items added")
    except Exception as e:
        print(f"❌ Error adding portfolio items: {str(e)}")
    
    # Display portfolio
    print("\n📋 Current Portfolio:")
    try:
        portfolio = db.get_portfolio()
        if not portfolio.empty:
            for _, row in portfolio.iterrows():
                print(f"  {row['symbol']}: {row['shares']} shares @ ${row['avg_price']:.2f}")
        else:
            print("  Portfolio is empty")
    except Exception as e:
        print(f"❌ Error displaying portfolio: {str(e)}")
    
    # Display transactions
    print("\n📝 Recent Transactions:")
    try:
        transactions = db.get_transactions()
        if not transactions.empty:
            for _, row in transactions.head(5).iterrows():
                print(f"  {row['transaction_type']} {row['shares']} {row['symbol']} @ ${row['price']:.2f}")
        else:
            print("  No transactions found")
    except Exception as e:
        print(f"❌ Error displaying transactions: {str(e)}")

def demo_analysis_tools():
    """Demonstrate analysis capabilities"""
    print_section("Analysis Tools Demo")
    
    analysis_tool = AnalysisTool()
    
    # Get portfolio data for analysis
    db = FinanceDatabase(Config().DATABASE_PATH)
    portfolio = db.get_portfolio()
    
    if portfolio.empty:
        print("❌ Portfolio is empty - cannot run analysis")
        return
    
    # Get current prices
    market_data = MarketDataTool()
    symbols = portfolio['symbol'].tolist()
    current_prices = market_data.get_portfolio_prices(symbols)
    
    # Convert portfolio to dict format
    portfolio_dict = {}
    for _, row in portfolio.iterrows():
        portfolio_dict[row['symbol']] = {
            'shares': row['shares'],
            'avg_price': row['avg_price']
        }
    
    # Calculate portfolio metrics
    print("📊 Calculating portfolio metrics...")
    try:
        metrics = analysis_tool.calculate_portfolio_metrics(portfolio_dict, current_prices)
        if "error" not in metrics:
            print(f"✅ Total Value: ${metrics['total_value']:,.2f}")
            print(f"✅ Total P&L: ${metrics['total_pnl']:+,.2f}")
            print(f"✅ Total Return: {metrics['total_return']*100:+.2f}%")
        else:
            print(f"❌ Error: {metrics['error']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Suggest rebalancing
    print("\n⚖️ Suggesting rebalancing...")
    try:
        rebalancing = analysis_tool.suggest_rebalancing(portfolio_dict, current_prices)
        if "error" not in rebalancing:
            print(f"✅ Total adjustment needed: ${rebalancing['total_adjustment']:,.2f}")
            for symbol, action in rebalancing['rebalancing_actions'].items():
                if action['action'] != 'HOLD':
                    print(f"  {symbol}: {action['action']} ${abs(action['dollar_adjustment']):,.2f}")
        else:
            print(f"❌ Error: {rebalancing['error']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def demo_notification_system():
    """Demonstrate notification capabilities"""
    print_section("Notification System Demo")
    
    notification_system = NotificationSystem()
    
    # Check notification status
    print("📱 Checking notification system status...")
    try:
        status = notification_system.get_notification_status()
        print(f"✅ System running: {status['running']}")
        print(f"✅ Pushover configured: {status['pushover_configured']}")
        print(f"✅ Active alerts: {status['active_alerts']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test notification (if configured)
    if status.get('pushover_configured'):
        print("\n🧪 Sending test notification...")
        try:
            success = notification_system.test_notification()
            if success:
                print("✅ Test notification sent successfully")
            else:
                print("❌ Failed to send test notification")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    else:
        print("\n⚠️ Pushover not configured - skipping test notification")
    
    # Add sample alerts
    print("\n🔔 Adding sample price alerts...")
    try:
        db = FinanceDatabase(Config().DATABASE_PATH)
        db.add_alert("AAPL", "PRICE_DROP", 5.0)
        db.add_alert("TSLA", "VOLATILITY", 10.0)
        print("✅ Sample alerts added")
    except Exception as e:
        print(f"❌ Error adding alerts: {str(e)}")

def demo_ai_agent():
    """Demonstrate AI agent capabilities"""
    print_section("AI Agent Demo")
    
    ai_agent = FinanceCopilotAgent()
    
    # Check agent status
    print("🤖 Checking AI agent status...")
    try:
        status = ai_agent.get_agent_status()
        print(f"✅ OpenAI configured: {status['openai_configured']}")
        print(f"✅ Available tools: {status['available_tools']}")
        print(f"✅ Database connected: {status['database_connected']}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test AI query (if OpenAI is configured)
    if status.get('openai_configured'):
        print("\n💬 Testing AI query...")
        try:
            query = "What's my current portfolio performance?"
            print(f"Query: {query}")
            
            response = ai_agent.process_query(query)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    else:
        print("\n⚠️ OpenAI not configured - skipping AI query test")
    
    # Show available functions
    print("\n🛠️ Available AI functions:")
    try:
        functions = ai_agent.get_available_functions()
        for func in functions[:5]:  # Show first 5
            print(f"  • {func['name']}: {func['description']}")
        if len(functions) > 5:
            print(f"  ... and {len(functions) - 5} more")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def demo_integration():
    """Demonstrate system integration"""
    print_section("System Integration Demo")
    
    print("🔄 Testing system integration...")
    
    try:
        # Initialize all components
        config = Config()
        db = FinanceDatabase(config.DATABASE_PATH)
        market_data = MarketDataTool()
        analysis_tool = AnalysisTool()
        notification_system = NotificationSystem()
        ai_agent = FinanceCopilotAgent()
        
        print("✅ All components initialized successfully")
        
        # Test data flow
        print("\n📊 Testing data flow...")
        
        # Get portfolio
        portfolio = db.get_portfolio()
        if not portfolio.empty:
            symbols = portfolio['symbol'].tolist()
            
            # Get market data
            current_prices = market_data.get_portfolio_prices(symbols)
            
            # Run analysis
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            metrics = analysis_tool.calculate_portfolio_metrics(portfolio_dict, current_prices)
            
            if "error" not in metrics:
                print(f"✅ Data flow successful - Portfolio value: ${metrics['total_value']:,.2f}")
            else:
                print(f"❌ Analysis error: {metrics['error']}")
        else:
            print("⚠️ Portfolio is empty - data flow test skipped")
        
        print("✅ System integration test completed")
        
    except Exception as e:
        print(f"❌ Integration error: {str(e)}")

def main():
    """Main demo function"""
    print_header("Finance Copilot Demo")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demos
        demo_market_data()
        demo_portfolio_management()
        demo_analysis_tools()
        demo_notification_system()
        demo_ai_agent()
        demo_integration()
        
        print_header("Demo Completed Successfully!")
        print("🎉 All demos completed successfully!")
        print("\nNext steps:")
        print("1. Set up your API keys in a .env file")
        print("2. Run 'python app.py' to start the web interface")
        print("3. Open http://localhost:7860 in your browser")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {str(e)}")
        print("Check your configuration and try again")

if __name__ == "__main__":
    main()




