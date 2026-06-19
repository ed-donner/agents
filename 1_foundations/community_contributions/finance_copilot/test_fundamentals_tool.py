#!/usr/bin/env python3
"""
Focused test for the get_stock_fundamentals tool
This script specifically tests the tool that was mentioned in the error
"""

import sys
import os
import json

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fundamentals_tool_directly():
    """Test the fundamentals tool directly from market_data.py"""
    print("🔍 Testing get_stock_fundamentals tool directly...")
    
    try:
        from market_data import MarketDataTool
        from config import Config
        
        config = Config()
        market_data = MarketDataTool()
        
        print(f"✅ Market data tool initialized")
        print(f"   Alpha Vantage API Key: {'✅ Set' if config.ALPHA_VANTAGE_API_KEY else '❌ Not set'}")
        
        # Test with AAPL
        print(f"\n📊 Testing with AAPL...")
        result = market_data.get_stock_fundamentals("AAPL")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        print(f"✅ Success! Retrieved fundamentals for AAPL")
        print(f"   Company: {result.get('company_name', 'N/A')}")
        print(f"   Sector: {result.get('sector', 'N/A')}")
        print(f"   Industry: {result.get('industry', 'N/A')}")
        print(f"   Market Cap: ${result.get('market_cap', 0):,.0f}")
        print(f"   PE Ratio: {result.get('pe_ratio', 'N/A')}")
        print(f"   Price to Book: {result.get('price_to_book', 'N/A')}")
        print(f"   Dividend Yield: {result.get('dividend_yield', 'N/A')}")
        print(f"   Return on Equity: {result.get('return_on_equity', 'N/A')}")
        print(f"   Debt to Equity: {result.get('debt_to_equity', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fundamentals_tool_via_agent():
    """Test the fundamentals tool through the AI agent"""
    print(f"\n🤖 Testing get_stock_fundamentals tool via AI Agent...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print(f"✅ AI Agent initialized")
        
        # Find the tool
        tool = None
        for t in agent.tools:
            if t.name == "get_stock_fundamentals":
                tool = t
                break
        
        if not tool:
            print(f"❌ Tool 'get_stock_fundamentals' not found in agent")
            return False
        
        print(f"✅ Found tool: {tool.name}")
        print(f"   Description: {tool.description}")
        
        # Test the tool
        print(f"\n📊 Testing tool execution...")
        result = agent._get_stock_fundamentals("AAPL")
        
        print(f"   Raw result: {result[:500]}...")
        
        # Try to parse as JSON
        try:
            parsed_result = json.loads(result)
            print(f"   ✅ Successfully parsed as JSON")
            
            if "error" in parsed_result:
                print(f"   ❌ Tool returned error: {parsed_result['error']}")
                return False
            
            print(f"   ✅ Tool execution successful")
            print(f"   Company: {parsed_result.get('company_name', 'N/A')}")
            print(f"   PE Ratio: {parsed_result.get('pe_ratio', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse result as JSON: {e}")
            print(f"   Result type: {type(result)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yfinance_directly():
    """Test yfinance directly to see if it's working"""
    print(f"\n📈 Testing yfinance directly...")
    
    try:
        import yfinance as yf
        
        print(f"✅ yfinance imported successfully")
        
        # Test with AAPL
        ticker = yf.Ticker("AAPL")
        print(f"✅ Ticker object created for AAPL")
        
        # Get info
        info = ticker.info
        print(f"✅ Ticker info retrieved")
        
        # Check key fields
        key_fields = ['longName', 'sector', 'industry', 'marketCap', 'trailingPE']
        for field in key_fields:
            value = info.get(field, 'N/A')
            print(f"   {field}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"❌ yfinance not installed: {e}")
        return False
    except Exception as e:
        print(f"❌ yfinance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Fundamentals Tool Debug Test")
    print("=" * 60)
    
    tests = [
        ("yfinance Direct Test", test_yfinance_directly),
        ("Fundamentals Tool Direct Test", test_fundamentals_tool_directly),
        ("Fundamentals Tool via Agent Test", test_fundamentals_tool_via_agent)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("📋 DEBUG TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed < total:
        print(f"\n🔍 RECOMMENDATIONS:")
        if not results.get("yfinance Direct Test", False):
            print(f"   - Install yfinance: pip install yfinance")
        if not results.get("Fundamentals Tool Direct Test", False):
            print(f"   - Check market_data.py implementation")
        if not results.get("Fundamentals Tool via Agent Test", False):
            print(f"   - Check AI agent tool wrapper")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


