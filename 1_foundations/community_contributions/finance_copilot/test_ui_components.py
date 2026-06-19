#!/usr/bin/env python3
"""
Test UI Components for Finance Copilot
Check if UI components are being created correctly
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ui_components():
    """Test if UI components are created correctly"""
    print("🧪 Testing UI Components...")
    
    try:
        from app import FinanceCopilotApp
        
        print("✅ App imported successfully")
        
        # Create the app instance
        app = FinanceCopilotApp()
        print("✅ App instance created successfully")
        
        # Check if AI agent is available
        if hasattr(app, 'ai_agent'):
            print(f"✅ AI Agent available with {len(app.ai_agent.tools)} tools")
        else:
            print("❌ AI Agent not found")
            return False
        
        # Check if UI components are created
        if hasattr(app, 'available_functions_output'):
            print("✅ Available functions output component created")
        else:
            print("❌ Available functions output component not found")
            return False
        
        if hasattr(app, 'agent_status_output'):
            print("✅ Agent status output component created")
        else:
            print("❌ Agent status output component not found")
            return False
        
        if hasattr(app, 'ai_response_output'):
            print("✅ AI response output component created")
        else:
            print("❌ AI response output component not found")
            return False
        
        # Test the methods
        try:
            functions = app.load_available_functions()
            print(f"✅ Load available functions works: {len(functions)} functions")
        except Exception as e:
            print(f"❌ Load available functions failed: {e}")
            return False
        
        try:
            status = app.load_agent_status()
            print(f"✅ Load agent status works: {len(status)} status items")
        except Exception as e:
            print(f"❌ Load agent status failed: {e}")
            return False
        
        try:
            refresh_result = app.refresh_ai_assistant_data()
            print(f"✅ Refresh AI assistant data works: {len(refresh_result)} results")
        except Exception as e:
            print(f"❌ Refresh AI assistant data failed: {e}")
            return False
        
        print("✅ All UI components test passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_agent_methods():
    """Test AI agent methods directly"""
    print("\n🤖 Testing AI Agent Methods...")
    
    try:
        from ai_agent import FinanceCopilotAgent
        
        agent = FinanceCopilotAgent()
        print("✅ AI Agent created successfully")
        
        # Test get_available_functions
        functions = agent.get_available_functions()
        print(f"✅ Available functions: {len(functions)}")
        for func in functions[:3]:  # Show first 3
            print(f"   - {func['name']}: {func['description'][:50]}...")
        
        # Test get_agent_status
        status = agent.get_agent_status()
        print(f"✅ Agent status: {len(status)} items")
        for key, value in status.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Agent methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - UI Components Test")
    print("=" * 50)
    
    ui_test = test_ui_components()
    ai_test = test_ai_agent_methods()
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if ui_test and ai_test:
        print("✅ All tests passed! UI components are working correctly.")
        print("\n🔍 If you still can't see the text areas and lists in the UI:")
        print("   1. Try refreshing the browser page")
        print("   2. Check browser console for JavaScript errors")
        print("   3. Try a different browser")
        print("   4. Check if Gradio is running on the correct port")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return ui_test and ai_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


