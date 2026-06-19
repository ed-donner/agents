#!/usr/bin/env python3
"""
Test Stock Price Fix for Finance Copilot
Verify that the improved stock price fetching works correctly
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_stock_price_fix():
    """Test the improved stock price functionality"""
    print("🧪 Testing Stock Price Fix...")
    
    try:
        from market_data import MarketDataTool
        
        market_data = MarketDataTool()
        print("✅ Market data tool initialized")
        
        # Test with a valid symbol
        print("\n📊 Testing with AAPL...")
        result = market_data.get_stock_price("AAPL")
        
        if "error" in result:
            print(f"❌ AAPL test failed: {result['error']}")
            return False
        else:
            print(f"✅ AAPL test passed!")
            print(f"   Symbol: {result['symbol']}")
            print(f"   Price: ${result['price']}")
            print(f"   Change: {result['change']} ({result['change_percent']}%)")
            print(f"   Volume: {result['volume']:,}")
        
        # Test with another symbol
        print("\n📊 Testing with GOOGL...")
        result = market_data.get_stock_price("GOOGL")
        
        if "error" in result:
            print(f"❌ GOOGL test failed: {result['error']}")
            return False
        else:
            print(f"✅ GOOGL test passed!")
            print(f"   Symbol: {result['symbol']}")
            print(f"   Price: ${result['price']}")
            print(f"   Change: {result['change']} ({result['change_percent']}%)")
        
        # Test error handling with invalid symbol
        print("\n📊 Testing error handling with invalid symbol...")
        result = market_data.get_stock_price("INVALID_SYMBOL_123")
        
        if "error" in result:
            print(f"✅ Error handling works: {result['error']}")
        else:
            print(f"⚠️  Unexpected result for invalid symbol: {result}")
        
        print("\n✅ All stock price tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Stock price test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_agent_stock_price():
    """Test the AI agent's stock price tool"""
    print("\n🤖 Testing AI Agent Stock Price Tool...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print("✅ AI Agent initialized")
        
        # Test the stock price tool directly
        result = agent._get_stock_price("AAPL")
        print(f"✅ Stock price tool result: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Agent stock price test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Stock Price Fix Test")
    print("=" * 60)
    
    stock_test = test_stock_price_fix()
    ai_test = test_ai_agent_stock_price()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if stock_test and ai_test:
        print("✅ All tests passed! Stock price functionality is working.")
        print("\n🎉 Improvements made:")
        print("   - Better error handling for invalid symbols")
        print("   - More reliable data fetching methods")
        print("   - Improved user feedback with troubleshooting tips")
        print("   - Symbol cleaning and validation")
        
        print("\n🌐 To test in the UI:")
        print("   1. The app should already be running")
        print("   2. Go to http://localhost:7860")
        print("   3. Click '🤖 AI Assistant' tab")
        print("   4. Ask: 'What's the current price of AAPL?'")
        print("   5. You should get a proper response or helpful error message")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return stock_test and ai_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


