#!/usr/bin/env python3
"""
Individual Tool Testing Script for Finance Copilot
Test specific tools to identify and fix issues
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")
    try:
        from config import Config
        config = Config()
        print(f"✅ Config loaded successfully")
        print(f"   Database path: {config.DATABASE_PATH}")
        print(f"   Alpha Vantage API Key: {'✅ Set' if config.ALPHA_VANTAGE_API_KEY else '❌ Not set'}")
        print(f"   OpenAI API Key: {'✅ Set' if config.OPENAI_API_KEY else '❌ Not set'}")
        print(f"   Pushover Keys: {'✅ Set' if config.PUSHOVER_USER_KEY and config.PUSHOVER_APP_TOKEN else '❌ Not set'}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🗄️  Testing Database...")
    try:
        from database import FinanceDatabase
        from config import Config
        
        config = Config()
        db = FinanceDatabase(config.DATABASE_PATH)
        print(f"✅ Database initialized successfully")
        
        # Test basic operations
        portfolio = db.get_portfolio()
        print(f"   Portfolio items: {len(portfolio)}")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_market_data():
    """Test market data tools"""
    print("\n📊 Testing Market Data Tools...")
    try:
        from market_data import MarketDataTool
        from config import Config
        
        config = Config()
        market_data = MarketDataTool()
        print(f"✅ Market data tool initialized")
        
        # Test stock price (this might fail without real API)
        try:
            result = market_data.get_stock_price("AAPL")
            if "error" in result:
                print(f"   ⚠️  Stock price test: {result['error']}")
            else:
                print(f"   ✅ Stock price test passed")
        except Exception as e:
            print(f"   ⚠️  Stock price test failed: {e}")
        
        # Test fundamentals
        try:
            result = market_data.get_stock_fundamentals("AAPL")
            if "error" in result:
                print(f"   ⚠️  Fundamentals test: {result['error']}")
            else:
                print(f"   ✅ Fundamentals test passed")
                print(f"      Company: {result.get('company_name', 'N/A')}")
                print(f"      PE Ratio: {result.get('pe_ratio', 'N/A')}")
        except Exception as e:
            print(f"   ⚠️  Fundamentals test failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_analysis_tool():
    """Test analysis tools"""
    print("\n📈 Testing Analysis Tools...")
    try:
        from analysis_tool import AnalysisTool
        
        analysis = AnalysisTool()
        print(f"✅ Analysis tool initialized")
        
        # Test portfolio metrics calculation
        portfolio = {
            'AAPL': {'shares': 100, 'avg_price': 150.00},
            'GOOGL': {'shares': 50, 'avg_price': 2800.00}
        }
        current_prices = {'AAPL': 160.00, 'GOOGL': 2900.00}
        
        try:
            metrics = analysis.calculate_portfolio_metrics(portfolio, current_prices)
            if "error" in metrics:
                print(f"   ⚠️  Portfolio metrics test: {metrics['error']}")
            else:
                print(f"   ✅ Portfolio metrics test passed")
                print(f"      Total Value: ${metrics.get('total_value', 0):,.2f}")
                print(f"      Total P&L: ${metrics.get('total_pnl', 0):,.2f}")
        except Exception as e:
            print(f"   ⚠️  Portfolio metrics test failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Analysis tool test failed: {e}")
        return False

def test_notification_system():
    """Test notification system"""
    print("\n🔔 Testing Notification System...")
    try:
        from notification_system import NotificationSystem
        from config import Config
        
        config = Config()
        notification = NotificationSystem()
        print(f"✅ Notification system initialized")
        
        # Test notification (this will fail without real API keys)
        try:
            result = notification.send_notification("Test message", "Test title")
            print(f"   ✅ Notification test passed")
        except Exception as e:
            print(f"   ⚠️  Notification test failed (expected without API keys): {e}")
        
        return True
    except Exception as e:
        print(f"❌ Notification system test failed: {e}")
        return False

def test_ai_agent():
    """Test AI agent initialization and tools"""
    print("\n🤖 Testing AI Agent...")
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print(f"✅ AI Agent initialized successfully")
        print(f"   Available tools: {len(agent.tools)}")
        
        # List all available tools
        tool_names = [tool.name for tool in agent.tools]
        print(f"   Tools: {', '.join(tool_names)}")
        
        # Test a simple tool
        try:
            result = agent._get_portfolio()
            print(f"   ✅ Portfolio tool test passed")
        except Exception as e:
            print(f"   ⚠️  Portfolio tool test failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ AI Agent test failed: {e}")
        return False

def test_specific_tool(tool_name):
    """Test a specific tool by name"""
    print(f"\n🔍 Testing Specific Tool: {tool_name}")
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Find the tool
        tool = None
        for t in agent.tools:
            if t.name == tool_name:
                tool = t
                break
        
        if not tool:
            print(f"❌ Tool '{tool_name}' not found")
            return False
        
        print(f"✅ Found tool: {tool.name}")
        print(f"   Description: {tool.description}")
        
        # Test the tool based on its name
        if tool_name == "get_stock_price":
            result = agent._get_stock_price("AAPL")
            print(f"   Result: {result[:200]}...")
        elif tool_name == "get_stock_fundamentals":
            result = agent._get_stock_fundamentals("AAPL")
            print(f"   Result: {result[:200]}...")
        elif tool_name == "get_portfolio":
            result = agent._get_portfolio()
            print(f"   Result: {result}")
        elif tool_name == "get_market_summary":
            result = agent._get_market_summary()
            print(f"   Result: {result[:200]}...")
        else:
            print(f"   ⚠️  Manual testing required for {tool_name}")
        
        return True
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Individual Tool Testing")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Database", test_database),
        ("Market Data", test_market_data),
        ("Analysis Tools", test_analysis_tool),
        ("Notification System", test_notification_system),
        ("AI Agent", test_ai_agent)
    ]
    
    results = {}
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # If specific tool testing is requested
    if len(sys.argv) > 1:
        tool_name = sys.argv[1]
        print(f"\n🔍 Testing specific tool: {tool_name}")
        test_specific_tool(tool_name)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


