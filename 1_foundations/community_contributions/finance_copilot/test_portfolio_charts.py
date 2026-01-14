#!/usr/bin/env python3
"""
Test Portfolio Charts Functionality for Finance Copilot
Debug the create_portfolio_charts tool issue
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_analysis_tool_charts():
    """Test the analysis tool's create_portfolio_charts method directly"""
    print("🧪 Testing Analysis Tool Portfolio Charts...")
    
    try:
        from analysis_tool import AnalysisTool
        
        analysis_tool = AnalysisTool()
        print("✅ AnalysisTool created successfully")
        
        # Test with sample portfolio data
        portfolio_data = {
            "AAPL": {"shares": 10, "avg_price": 150.0},
            "GOOGL": {"shares": 5, "avg_price": 2800.0},
            "MSFT": {"shares": 8, "avg_price": 300.0}
        }
        
        current_prices = {
            "AAPL": {"price": 160.0, "error": None},
            "GOOGL": {"price": 2900.0, "error": None},
            "MSFT": {"price": 320.0, "error": None}
        }
        
        print(f"📊 Portfolio data: {portfolio_data}")
        print(f"💰 Current prices: {current_prices}")
        
        # Test the method
        charts = analysis_tool.create_portfolio_charts(portfolio_data, current_prices)
        
        if "error" in charts:
            print(f"❌ Error in create_portfolio_charts: {charts['error']}")
            return False
        
        print("✅ Charts created successfully!")
        print(f"📈 Charts returned: {list(charts.keys())}")
        
        # Check if expected chart objects are present
        expected_charts = ["allocation_chart", "returns_chart", "weights_chart"]
        for chart_name in expected_charts:
            if chart_name in charts:
                print(f"   ✅ {chart_name}: {type(charts[chart_name])}")
            else:
                print(f"   ❌ {chart_name}: Missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_agent_charts():
    """Test the AI agent's _create_portfolio_charts method"""
    print("\n" + "="*60)
    print("🤖 Testing AI Agent Portfolio Charts...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print("✅ FinanceCopilotAgent created successfully")
        
        # Test the method directly
        result = agent._create_portfolio_charts()
        print(f"📊 Result: {result}")
        
        if "Error:" in result:
            print(f"❌ Error in _create_portfolio_charts: {result}")
            return False
        
        print("✅ AI Agent portfolio charts method working!")
        return True
        
    except Exception as e:
        print(f"❌ AI Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_registration():
    """Test if the create_portfolio_charts tool is properly registered"""
    print("\n" + "="*60)
    print("🔧 Testing Tool Registration...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Get the tools list
        tools = agent.get_tools()
        
        # Check if create_portfolio_charts is registered
        tool_names = [tool.name for tool in tools]
        print(f"📋 Available tools: {tool_names}")
        
        if "create_portfolio_charts" in tool_names:
            print("✅ create_portfolio_charts tool is registered")
            
            # Find the tool and check its function
            for tool in tools:
                if tool.name == "create_portfolio_charts":
                    print(f"   Function: {tool.func}")
                    print(f"   Description: {tool.description}")
                    break
        else:
            print("❌ create_portfolio_charts tool is NOT registered")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    print("\n" + "="*60)
    print("📦 Testing Dependencies...")
    
    try:
        # Test plotly
        import plotly.graph_objects as go
        import plotly.express as px
        print("✅ Plotly imported successfully")
        
        # Test pandas
        import pandas as pd
        print("✅ Pandas imported successfully")
        
        # Test numpy
        import numpy as np
        print("✅ NumPy imported successfully")
        
        # Test matplotlib
        import matplotlib.pyplot as plt
        print("✅ Matplotlib imported successfully")
        
        # Test seaborn
        import seaborn as sns
        print("✅ Seaborn imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Portfolio Charts Debug Test")
    print("=" * 60)
    
    # Test 1: Dependencies
    deps_test = test_dependencies()
    
    # Test 2: Analysis tool
    analysis_test = test_analysis_tool_charts()
    
    # Test 3: Tool registration
    registration_test = test_tool_registration()
    
    # Test 4: AI Agent method
    agent_test = test_ai_agent_charts()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if deps_test and analysis_test and registration_test and agent_test:
        print("✅ All tests passed! Portfolio charts should work.")
        print("\n🎉 What's been verified:")
        print("   - All dependencies are available")
        print("   - Analysis tool creates charts correctly")
        print("   - Tool is properly registered in AI agent")
        print("   - AI agent method executes without errors")
        
        print("\n🔍 If you're still getting 'not implemented' error:")
        print("   - Check if there's a database connection issue")
        print("   - Verify portfolio data exists")
        print("   - Check for any recent code changes")
        
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
        if not deps_test:
            print("\n💡 Try installing missing dependencies:")
            print("   pip install plotly pandas numpy matplotlib seaborn")
        
        if not analysis_test:
            print("\n💡 Analysis tool issue - check analysis_tool.py")
        
        if not registration_test:
            print("\n💡 Tool registration issue - check ai_agent.py")
        
        if not agent_test:
            print("\n💡 AI agent issue - check database and market data")
    
    return deps_test and analysis_test and registration_test and agent_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
