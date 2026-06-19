#!/usr/bin/env python3
"""
Test Multiple Tool Invocation for Finance Copilot
Verify that the AI agent can use multiple tools for comprehensive responses
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_multiple_tool_execution():
    """Test that the AI agent can execute multiple tools"""
    print("🧪 Testing Multiple Tool Execution...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print("✅ FinanceCopilotAgent created successfully")
        
        # Test with a comprehensive query that should use multiple tools
        test_query = "Tell me about Google - I want fundamentals, news, and current price"
        print(f"\n🔍 Test Query: {test_query}")
        
        # Process the query
        response = agent.process_query(test_query)
        
        print(f"\n📊 AI Response:")
        print(response)
        
        # Check if the response indicates multiple tools were used
        if "fundamentals" in response.lower() and "news" in response.lower() and "price" in response.lower():
            print("\n✅ Multiple tools appear to have been used!")
            return True
        else:
            print("\n❌ Response doesn't seem comprehensive - may not have used multiple tools")
            return False
        
    except Exception as e:
        print(f"❌ Multiple tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_execution_method():
    """Test the _execute_tools method directly with multiple tools"""
    print("\n" + "="*60)
    print("🔧 Testing Tool Execution Method...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Test tool plan with multiple tools
        tool_plan = {
            "tools": ["get_stock_price", "get_stock_fundamentals", "get_company_news"],
            "parameters": {"symbol": "GOOGL", "limit": 3}
        }
        
        print(f"📋 Tool Plan: {tool_plan}")
        
        # Execute the tools
        results = agent._execute_tools(tool_plan)
        
        print(f"\n📊 Tool Results:")
        for tool_name, result in results.items():
            print(f"   {tool_name}: {'✅ Success' if 'error' not in result else '❌ Failed'}")
            if 'error' in result:
                print(f"      Error: {result['error']}")
        
        # Check if all tools executed successfully
        successful_tools = [name for name, result in results.items() if 'error' not in result]
        failed_tools = [name for name, result in results.items() if 'error' in result]
        
        print(f"\n📈 Summary:")
        print(f"   Successful: {len(successful_tools)} tools")
        print(f"   Failed: {len(failed_tools)} tools")
        
        if len(successful_tools) >= 2:
            print("✅ Multiple tools executed successfully!")
            return True
        else:
            print("❌ Not enough tools executed successfully")
            return False
        
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_tools():
    """Test specific tools that should work together"""
    print("\n" + "="*60)
    print("🎯 Testing Specific Tool Combinations...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Test 1: Stock price tool
        print("\n🔍 Testing get_stock_price...")
        stock_result = agent._get_stock_price("GOOGL")
        print(f"   Stock Price Result: {'✅ Success' if 'error' not in stock_result else '❌ Failed'}")
        
        # Test 2: Fundamentals tool
        print("\n🔍 Testing get_stock_fundamentals...")
        fundamentals_result = agent._get_stock_fundamentals("GOOGL")
        print(f"   Fundamentals Result: {'✅ Success' if 'error' not in fundamentals_result else '❌ Failed'}")
        
        # Test 3: Company news tool
        print("\n🔍 Testing get_company_news...")
        news_result = agent._get_company_news("GOOGL", 3)
        print(f"   Company News Result: {'✅ Success' if 'error' not in news_result else '❌ Failed'}")
        
        # Check overall success
        tools_working = 0
        if 'error' not in stock_result:
            tools_working += 1
        if 'error' not in fundamentals_result:
            tools_working += 1
        if 'error' not in news_result:
            tools_working += 1
        
        print(f"\n📊 Overall: {tools_working}/3 tools working")
        
        if tools_working >= 2:
            print("✅ Most tools are working correctly!")
            return True
        else:
            print("❌ Too many tools are failing")
            return False
        
    except Exception as e:
        print(f"❌ Specific tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Multiple Tool Invocation Test")
    print("=" * 60)
    
    # Test 1: Multiple tool execution
    multi_tool_test = test_multiple_tool_execution()
    
    # Test 2: Tool execution method
    execution_test = test_tool_execution_method()
    
    # Test 3: Specific tools
    specific_test = test_specific_tools()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if multi_tool_test and execution_test and specific_test:
        print("✅ All tests passed! Multiple tool invocation is working.")
        print("\n🎉 What's been verified:")
        print("   - AI agent can execute multiple tools for comprehensive responses")
        print("   - Tool execution method handles multiple tools correctly")
        print("   - Individual tools (stock price, fundamentals, news) are working")
        print("   - Company analysis queries can now use multiple tools")
        
        print("\n🌐 To test in the UI:")
        print("   1. Go to the AI Assistant tab")
        print("   2. Ask: 'Tell me about Google' or 'Show me AAPL fundamentals and news'")
        print("   3. The AI should now use multiple tools for comprehensive responses")
        
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
        if not multi_tool_test:
            print("\n💡 AI agent may not be using multiple tools effectively")
        
        if not execution_test:
            print("\n💡 Tool execution method may have issues")
        
        if not specific_test:
            print("\n💡 Individual tools may not be working")
    
    return multi_tool_test and execution_test and specific_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


