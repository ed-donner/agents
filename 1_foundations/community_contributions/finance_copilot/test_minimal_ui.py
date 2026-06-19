#!/usr/bin/env python3
"""
Minimal UI Test for Finance Copilot
Test basic UI functionality
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_minimal_ui():
    """Test minimal UI setup"""
    print("🧪 Testing Minimal UI...")
    
    try:
        from app import FinanceCopilotApp
        
        # Create app instance
        app = FinanceCopilotApp()
        print("✅ App created successfully")
        
        # Test basic methods
        functions = app.load_available_functions()
        print(f"✅ Functions loaded: {len(functions)}")
        
        status = app.load_agent_status()
        print(f"✅ Status loaded: {len(status)}")
        
        # Test refresh
        refresh_result = app.refresh_ai_assistant_data()
        print(f"✅ Refresh result: {len(refresh_result)}")
        
        # Test force refresh
        force_result = app.force_refresh_ai_assistant()
        print(f"✅ Force refresh result: {len(force_result)}")
        
        print("✅ All UI tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_ui()
    if success:
        print("\n🎉 UI is working correctly!")
        print("If you still can't see the components in the browser:")
        print("1. Try refreshing the page")
        print("2. Check browser console for errors")
        print("3. Try a different browser")
        print("4. Make sure you're accessing the correct URL")
    else:
        print("\n❌ UI has issues that need to be fixed")
    
    sys.exit(0 if success else 1)


