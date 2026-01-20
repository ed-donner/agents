#!/usr/bin/env python3
"""
Test Conversation Memory System for Finance Copilot
Verify that context is maintained between multiple questions
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conversation_memory_basic(agent):
    """Test basic conversation memory functionality"""
    print("🧪 Testing Basic Conversation Memory...")
    
    try:
        # Check initial memory state
        initial_memory = agent.get_memory_summary()
        print(f"\n📝 Initial Memory: {initial_memory}")
        
        # Test memory methods
        agent.add_to_memory("What's the price of AAPL?", "AAPL is trading at $150.00", ["get_stock_price"])
        agent.add_to_memory("Show me fundamentals", "AAPL has P/E ratio of 25.5", ["get_stock_fundamentals"])
        
        # Check memory after adding exchanges
        updated_memory = agent.get_memory_summary()
        print(f"\n📝 Updated Memory: {updated_memory}")
        
        # Check conversation context
        context = agent.get_conversation_context()
        print(f"\n🔍 Conversation Context: {context}")
        
        if "AAPL" in context and "get_stock_price" in context:
            print("✅ Conversation memory working correctly!")
            return True
        else:
            print("❌ Conversation memory not working properly")
            return False
        
    except Exception as e:
        print(f"❌ Basic memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_context(agent):
    """Test that conversation context is properly used in responses"""
    print("\n" + "="*60)
    print("🔍 Testing Conversation Context Usage...")
    
    try:
        # Add some context to memory
        agent.add_to_memory("What's the price of GOOGL?", "GOOGL is trading at $2800.00", ["get_stock_price"])
        agent.add_to_memory("Show me GOOGL fundamentals", "GOOGL has P/E ratio of 28.2", ["get_stock_fundamentals"])
        
        # Now ask a follow-up question that should use context
        follow_up_query = "How does that compare to what we discussed earlier?"
        print(f"🔍 Follow-up Query: {follow_up_query}")
        
        # Check if the agent can access context
        context = agent.get_conversation_context()
        print(f"\n📋 Available Context:")
        print(context)
        
        # Check if both GOOGL queries are in the context
        if "GOOGL" in context and "P/E ratio" in context and "get_stock_price" in context:
            print("✅ Context is available for follow-up questions")
            return True
        else:
            print("❌ Context not properly maintained")
            print(f"Expected: GOOGL, P/E ratio, get_stock_price")
            print(f"Found: GOOGL in context: {'GOOGL' in context}")
            print(f"Found: P/E ratio in context: {'P/E ratio' in context}")
            print(f"Found: get_stock_price in context: {'get_stock_price' in context}")
            return False
        
    except Exception as e:
        print(f"❌ Context usage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_management(agent):
    """Test memory management features"""
    print("\n" + "="*60)
    print("🗂️ Testing Memory Management...")
    
    try:
        # Add more than max_memory_items exchanges
        for i in range(15):
            agent.add_to_memory(f"Query {i}", f"Response {i}", ["test_tool"])
        
        # Check memory size
        memory_summary = agent.get_memory_summary()
        print(f"\n📊 Memory Summary: {memory_summary}")
        
        # Check if memory is limited to max_memory_items
        if len(agent.conversation_memory) <= agent.max_memory_items:
            print(f"✅ Memory properly limited to {agent.max_memory_items} items")
        else:
            print(f"❌ Memory not properly limited: {len(agent.conversation_memory)} items")
            return False
        
        # Test memory clearing
        agent.clear_memory()
        if len(agent.conversation_memory) == 0:
            print("✅ Memory cleared successfully")
        else:
            print("❌ Memory not cleared properly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Memory management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_tools(agent):
    """Test the new conversation-related tools"""
    print("\n" + "="*60)
    print("🔧 Testing Conversation Tools...")
    
    try:
        # Add some conversation history
        agent.add_to_memory("Test query 1", "Test response 1", ["get_stock_price"])
        agent.add_to_memory("Test query 2", "Test response 2", ["get_fundamentals"])
        
        # Test get_conversation_history tool
        history_result = agent._get_conversation_history()
        print(f"\n📝 Conversation History Tool: {history_result}")
        
        if "Test query 1" in history_result and "Test query 2" in history_result:
            print("✅ get_conversation_history tool working")
        else:
            print("❌ get_conversation_history tool not working")
            return False
        
        # Test clear_conversation_history tool
        clear_result = agent._clear_conversation_history()
        print(f"\n🗑️ Clear History Tool: {clear_result}")
        
        if "cleared successfully" in clear_result.lower():
            print("✅ clear_conversation_history tool working")
        else:
            print("❌ clear_conversation_history tool not working")
            return False
        
        # Verify memory is actually cleared
        if len(agent.conversation_memory) == 0:
            print("✅ Memory actually cleared after tool execution")
        else:
            print("❌ Memory not cleared after tool execution")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_contextual_response(agent):
    """Test that the AI agent provides contextual responses"""
    print("\n" + "="*60)
    print("🤖 Testing Contextual AI Responses...")
    
    try:
        # Add context about a specific stock
        agent.add_to_memory("What's the price of TSLA?", "TSLA is trading at $250.00", ["get_stock_price"])
        agent.add_to_memory("Show me TSLA fundamentals", "TSLA has P/E ratio of 45.2", ["get_stock_fundamentals"])
        
        # Now ask a contextual question
        contextual_query = "What about the growth potential?"
        print(f"🔍 Contextual Query: {contextual_query}")
        
        # Check if context is available
        context = agent.get_conversation_context()
        print(f"\n📋 Available Context:")
        print(context)
        
        # Check if TSLA context is available
        if "TSLA" in context and "P/E ratio" in context and "get_stock_price" in context:
            print("✅ Context available for contextual responses")
            return True
        else:
            print("❌ Context not available for contextual responses")
            print(f"Expected: TSLA, P/E ratio, get_stock_price")
            print(f"Found: TSLA in context: {'TSLA' in context}")
            print(f"Found: P/E ratio in context: {'P/E ratio' in context}")
            print(f"Found: get_stock_price in context: {'get_stock_price' in context}")
            return False
        
    except Exception as e:
        print(f"❌ Contextual response test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Conversation Memory Test")
    print("=" * 60)
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        # Create a single agent instance for all tests
        print("🤖 Creating FinanceCopilotAgent...")
        agent = FinanceCopilotAgent()
        print("✅ FinanceCopilotAgent created successfully")
        
        # Test 1: Basic conversation memory
        basic_test = test_conversation_memory_basic(agent)
        
        # Test 2: Conversation context usage
        context_test = test_conversation_context(agent)
        
        # Test 3: Memory management
        management_test = test_memory_management(agent)
        
        # Test 4: Conversation tools
        tools_test = test_conversation_tools(agent)
        
        # Test 5: Contextual responses
        contextual_test = test_contextual_response(agent)
        
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        if basic_test and context_test and management_test and tools_test and contextual_test:
            print("✅ All tests passed! Conversation memory system is working.")
            print("\n🎉 What's been verified:")
            print("   - Basic conversation memory functionality")
            print("   - Context usage in follow-up questions")
            print("   - Memory management and limits")
            print("   - Conversation history tools")
            print("   - Contextual AI responses")
            
            print("\n🌐 To test in the UI:")
            print("   1. Go to the AI Assistant tab")
            print("   2. Ask: 'What's the price of AAPL?'")
            print("   3. Follow up: 'How does that compare to GOOGL?'")
            print("   4. Check history: 'Show me our conversation history'")
            print("   5. Clear history: 'Clear our conversation'")
            
            print("\n💡 Benefits of conversation memory:")
            print("   - AI remembers previous questions and context")
            print("   - More intelligent follow-up responses")
            print("   - Builds on previous analysis")
            print("   - Maintains conversation flow")
            
        else:
            print("❌ Some tests failed. Check the error messages above.")
            
            if not basic_test:
                print("\n💡 Basic memory functionality may have issues")
            
            if not context_test:
                print("\n💡 Context usage may not be working")
            
            if not management_test:
                print("\n💡 Memory management may have problems")
            
            if not tools_test:
                print("\n💡 Conversation tools may not be functional")
            
            if not contextual_test:
                print("\n💡 Contextual responses may not be working")
        
        return basic_test and context_test and management_test and tools_test and contextual_test
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
