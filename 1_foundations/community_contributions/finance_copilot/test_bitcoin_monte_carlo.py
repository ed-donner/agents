#!/usr/bin/env python3
"""
Test script for Bitcoin Monte Carlo simulation
Tests the specific query: "what is the outlook for bitcoin in year 2025"
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agent import FinanceCopilotAgent

def test_bitcoin_monte_carlo():
    """Test the Bitcoin Monte Carlo simulation directly"""
    print("🧪 Testing Bitcoin Monte Carlo Simulation")
    print("=" * 50)
    
    # Initialize the AI agent
    print("🔧 Initializing AI agent...")
    agent = FinanceCopilotAgent()
    
    if not agent.llm:
        print("❌ OpenAI LLM not available. Please check your API key.")
        return
    
    # Test query
    test_query = "what is the outlook for bitcoin in year 2025"
    print(f"📝 Test Query: {test_query}")
    print()
    
    try:
        # Process the query
        print("🔄 Processing query...")
        response = agent.process_query(test_query)
        
        print("✅ Query processed successfully!")
        print(f"📊 Response length: {len(response)} characters")
        print()
        print("📋 Full Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        import traceback
        print("🔍 Full traceback:")
        traceback.print_exc()

def test_monte_carlo_tool_directly():
    """Test the Monte Carlo tool directly without the full query processing"""
    print("\n🧪 Testing Monte Carlo Tool Directly")
    print("=" * 50)
    
    # Initialize the AI agent
    print("🔧 Initializing AI agent...")
    agent = FinanceCopilotAgent()
    
    try:
        # Test the tool directly
        print("🔧 Testing run_symbol_monte_carlo_simulation tool...")
        result = agent._run_symbol_monte_carlo_simulation("BTC", 5, 10000)
        
        print("✅ Tool executed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result length: {len(str(result))} characters")
        print()
        print("📋 Tool Result:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        # Try to parse as JSON if it's a string
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                print("✅ JSON parsing successful!")
                print(f"📊 Parsed result keys: {list(parsed.keys())}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
        
    except Exception as e:
        print(f"❌ Error testing tool directly: {e}")
        import traceback
        print("🔍 Full traceback:")
        traceback.print_exc()

def test_tool_execution():
    """Test the tool execution logic"""
    print("\n🧪 Testing Tool Execution Logic")
    print("=" * 50)
    
    # Initialize the AI agent
    print("🔧 Initializing AI agent...")
    agent = FinanceCopilotAgent()
    
    try:
        # Create a tool plan similar to what the AI would generate
        tool_plan = {
            "tools": ["get_crypto_price", "run_symbol_monte_carlo_simulation"],
            "parameters": {"symbol": "BTC", "years": 5, "simulations": 10000},
            "reasoning": "Bitcoin outlook query",
            "expected_output": "Bitcoin price and Monte Carlo simulation"
        }
        
        print(f"🎯 Tool plan: {tool_plan}")
        print()
        
        # Execute tools
        print("🔧 Executing tools...")
        results = agent._execute_tools(tool_plan)
        
        print("✅ Tools executed successfully!")
        print(f"📊 Results keys: {list(results.keys())}")
        print()
        
        # Show results for each tool
        for tool_name, result in results.items():
            print(f"📋 {tool_name}:")
            print(f"   Type: {type(result)}")
            print(f"   Content: {str(result)[:200]}...")
            print()
        
    except Exception as e:
        print(f"❌ Error testing tool execution: {e}")
        import traceback
        print("🔍 Full traceback:")
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🚀 Bitcoin Monte Carlo Simulation Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Full query processing
    test_bitcoin_monte_carlo()
    
    # Test 2: Direct tool execution
    test_monte_carlo_tool_directly()
    
    # Test 3: Tool execution logic
    test_tool_execution()
    
    print("\n🏁 Test suite completed!")

if __name__ == "__main__":
    main()


