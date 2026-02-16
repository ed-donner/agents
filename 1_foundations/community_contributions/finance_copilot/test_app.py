#!/usr/bin/env python3
"""
Simple test script to check if Finance Copilot app initializes correctly
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_app_initialization():
    """Test if the app can be initialized without errors"""
    try:
        print("🧪 Testing Finance Copilot app initialization...")
        
        # Test imports
        print("📦 Testing imports...")
        from config import Config
        print("✅ Config imported successfully")
        
        from database import FinanceDatabase
        print("✅ Database imported successfully")
        
        from market_data import MarketDataTool
        print("✅ Market data tool imported successfully")
        
        from analysis_tool import AnalysisTool
        print("✅ Analysis tool imported successfully")
        
        from notification_system import NotificationSystem
        print("✅ Notification system imported successfully")
        
        from ai_agent import FinanceCopilotAgent
        print("✅ AI agent imported successfully")
        
        # Test app initialization
        print("🚀 Testing app initialization...")
        from app import FinanceCopilotApp
        
        # Create app instance
        app = FinanceCopilotApp()
        print("✅ FinanceCopilotApp created successfully")
        
        print("\n🎉 All tests passed! The app should work correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_initialization()
    if success:
        print("\n✅ Ready to run: python app.py")
    else:
        print("\n❌ Fix the errors above before running the app")
