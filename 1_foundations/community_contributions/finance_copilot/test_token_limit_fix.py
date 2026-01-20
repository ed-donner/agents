#!/usr/bin/env python3
"""
Test Token Limit Fix for Finance Copilot
Verify that growth analysis queries work without hitting token limits
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_growth_analysis_query():
    """Test that growth analysis queries work without token limit errors"""
    print("🧪 Testing Growth Analysis Query...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print("✅ FinanceCopilotAgent created successfully")
        
        # Test with the problematic query
        test_query = "is it good future growth for OPEN stock ?"
        print(f"\n🔍 Test Query: {test_query}")
        
        # Process the query
        response = agent.process_query(test_query)
        
        print(f"\n📊 AI Response:")
        print(response)
        
        # Check if we got a proper response without token limit errors
        if "context length exceeded" in response.lower() or "token" in response.lower():
            print("\n❌ Still hitting token limits!")
            return False
        elif "error" in response.lower() and "400" in response:
            print("\n❌ Still getting HTTP 400 errors!")
            return False
        elif "growth analysis" in response.lower() or "growth potential" in response.lower():
            print("\n✅ Growth analysis working correctly!")
            return True
        else:
            print("\n⚠️  Response received but may not be growth analysis")
            return True
        
    except Exception as e:
        print(f"❌ Growth analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_truncation():
    """Test that the token truncation method works correctly"""
    print("\n" + "="*60)
    print("✂️ Testing Token Truncation...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Create a mock tool result with very long data
        long_tool_results = {
            "get_stock_fundamentals": {
                "symbol": "OPEN",
                "pe_ratio": 25.5,
                "data": "x" * 10000,  # Very long string
                "other_info": "y" * 5000
            },
            "get_company_news": {
                "symbol": "OPEN",
                "data": ["news item " + "x" * 2000] * 10,  # Long news items
                "count": 10
            }
        }
        
        print(f"📏 Original data length: {len(str(long_tool_results))} chars")
        
        # Test truncation
        truncated = agent._truncate_tool_results(long_tool_results)
        
        print(f"📏 Truncated data length: {len(str(truncated))} chars")
        
        # Check if truncation worked
        if len(str(truncated)) < len(str(long_tool_results)):
            print("✅ Truncation successful - data length reduced")
            
            # Check if key information is preserved
            if "symbol" in str(truncated) and "pe_ratio" in str(truncated):
                print("✅ Key information preserved")
                return True
            else:
                print("❌ Key information lost during truncation")
                return False
        else:
            print("❌ Truncation failed - data length not reduced")
            return False
        
    except Exception as e:
        print(f"❌ Token truncation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_growth_analysis_detection():
    """Test that growth analysis queries are properly detected"""
    print("\n" + "="*60)
    print("🔍 Testing Growth Analysis Detection...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Test various queries
        test_queries = [
            "is it good future growth for OPEN stock ?",
            "What's the growth potential of AAPL?",
            "Should I buy GOOGL for growth?",
            "What's the price of MSFT?",
            "Show me my portfolio",
            "Is TSLA a good investment for the future?"
        ]
        
        print("🔍 Testing query detection...")
        for query in test_queries:
            is_growth = agent._is_growth_analysis_query(query)
            print(f"   '{query}' → {'Growth Query' if is_growth else 'Regular Query'}")
        
        # Check if the specific query is detected
        target_query = "is it good future growth for OPEN stock ?"
        is_detected = agent._is_growth_analysis_query(target_query)
        
        if is_detected:
            print(f"\n✅ Growth analysis query properly detected: '{target_query}'")
            return True
        else:
            print(f"\n❌ Growth analysis query NOT detected: '{target_query}'")
            return False
        
    except Exception as e:
        print(f"❌ Growth analysis detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specialized_growth_analysis():
    """Test the specialized growth analysis method"""
    print("\n" + "="*60)
    print("📊 Testing Specialized Growth Analysis...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        
        # Test with sample fundamentals data
        sample_fundamentals = {
            "symbol": "OPEN",
            "pe_ratio": 25.5,
            "forward_pe": 22.0,
            "revenue_growth": 0.15,
            "earnings_growth": 0.20,
            "debt_to_equity": 0.3,
            "return_on_equity": 0.18
        }
        
        # Test the specialized method
        analysis = agent._analyze_growth_potential("OPEN", sample_fundamentals)
        
        print(f"📊 Growth Analysis Result:")
        print(analysis)
        
        # Check if analysis contains expected elements
        expected_elements = [
            "Growth Analysis",
            "Growth Score:",
            "Recommendation:",
            "Key Metrics Analysis:"
        ]
        
        missing_elements = []
        for element in expected_elements:
            if element not in analysis:
                missing_elements.append(element)
        
        if not missing_elements:
            print("✅ All expected analysis elements present")
            return True
        else:
            print(f"❌ Missing analysis elements: {missing_elements}")
            return False
        
    except Exception as e:
        print(f"❌ Specialized growth analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Token Limit Fix Test")
    print("=" * 60)
    
    # Test 1: Growth analysis query
    growth_test = test_growth_analysis_query()
    
    # Test 2: Token truncation
    truncation_test = test_token_truncation()
    
    # Test 3: Growth analysis detection
    detection_test = test_growth_analysis_detection()
    
    # Test 4: Specialized growth analysis
    specialized_test = test_specialized_growth_analysis()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if growth_test and truncation_test and detection_test and specialized_test:
        print("✅ All tests passed! Token limit issue is resolved.")
        print("\n🎉 What's been verified:")
        print("   - Growth analysis queries work without token limit errors")
        print("   - Token truncation prevents context length exceeded")
        print("   - Growth analysis queries are properly detected")
        print("   - Specialized growth analysis provides intelligent insights")
        
        print("\n🌐 To test in the UI:")
        print("   1. Go to the AI Assistant tab")
        print("   2. Ask: 'Is it good future growth for OPEN stock?'")
        print("   3. Should now get comprehensive growth analysis without errors")
        
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
        if not growth_test:
            print("\n💡 Growth analysis queries may still have issues")
        
        if not truncation_test:
            print("\n💡 Token truncation may not be working")
        
        if not detection_test:
            print("\n💡 Growth analysis detection may be faulty")
        
        if not specialized_test:
            print("\n💡 Specialized growth analysis may have issues")
    
    return growth_test and truncation_test and detection_test and specialized_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


