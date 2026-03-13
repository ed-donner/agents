#!/usr/bin/env python3
"""
Test script for LLM integration in Finance Copilot
"""

import os
from dotenv import load_dotenv

def test_environment():
    """Test environment variables"""
    print("🔍 Testing LLM Environment Variables")
    print("=" * 50)
    
    load_dotenv()
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:8]}...{openai_key[-4:]}")
        print(f"   Length: {len(openai_key)} characters")
    else:
        print("❌ OPENAI_API_KEY: Not set")
        return False
    
    return True

def test_imports():
    """Test if required libraries can be imported"""
    print("\n🔍 Testing Library Imports")
    print("=" * 50)
    
    try:
        import openai
        version = getattr(openai, '__version__', 'Unknown version')
        print(f"✅ openai: {version}")
    except ImportError as e:
        print(f"❌ openai: {e}")
        return False
    
    try:
        import langchain
        version = getattr(langchain, '__version__', 'Unknown version')
        print(f"✅ langchain: {version}")
    except ImportError as e:
        print(f"❌ langchain: {e}")
        return False
    
    try:
        import langchain_openai
        # Try to get version, but don't fail if it doesn't exist
        try:
            version = langchain_openai.__version__
        except AttributeError:
            version = "Unknown version (no __version__ attribute)"
        print(f"✅ langchain_openai: {version}")
    except ImportError as e:
        print(f"❌ langchain_openai: {e}")
        print("💡 Try installing: pip install langchain-openai")
        return False
    
    return True

def test_ai_agent():
    """Test AI agent initialization"""
    print("\n🔍 Testing AI Agent")
    print("=" * 50)
    
    try:
        from ai_agent import FinanceCopilotAgent
        print("✅ FinanceCopilotAgent imported successfully")
        
        # Initialize the agent
        agent = FinanceCopilotAgent()
        print("✅ FinanceCopilotAgent initialized successfully")
        
        # Test LLM status
        llm_status = agent.get_llm_status()
        print("\n📊 LLM Status:")
        print(llm_status)
        
        # Test a simple query
        print("\n🧪 Testing Simple Query...")
        test_query = "What is the current price of AAPL?"
        print(f"Query: {test_query}")
        
        try:
            response = agent.process_query(test_query)
            print(f"✅ Response received (length: {len(response)} characters)")
            print(f"Response preview: {response[:200]}...")
        except Exception as e:
            print(f"❌ Query processing failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import FinanceCopilotAgent: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize FinanceCopilotAgent: {e}")
        return False

def test_direct_openai():
    """Test direct OpenAI API connection"""
    print("\n🔍 Testing Direct OpenAI API")
    print("=" * 50)
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ No API key available for testing")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test a simple completion
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            print("✅ Direct OpenAI API test successful")
            print(f"   Response: {response.choices[0].message.content}")
            return True
        except Exception as e:
            print(f"❌ Direct OpenAI API test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import OpenAI client: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Finance Copilot LLM Integration Test")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Library Imports", test_imports),
        ("Direct OpenAI API", test_direct_openai),
        ("AI Agent", test_ai_agent),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All LLM tests passed! Your AI integration is working correctly.")
        print("\n💡 You can now:")
        print("   1. Run the OAuth app: python3 run_working_oauth.py")
        print("   2. Test AI features in the Finance Copilot interface")
        print("   3. Ask questions like 'What is the growth potential of AAPL?'")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        
        if passed < 2:  # Environment or imports failed
            print("\n🔧 Common fixes:")
            print("   1. Check your .env file has OPENAI_API_KEY")
            print("   2. Install missing packages: pip install openai langchain-openai")
            print("   3. Verify your OpenAI API key is valid")
        
        if passed == 3:  # Only AI agent failed
            print("\n🔧 AI Agent issues:")
            print("   1. Check the error messages above")
            print("   2. Verify your OpenAI API key has sufficient credits")
            print("   3. Check OpenAI service status")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
