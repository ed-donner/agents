#!/usr/bin/env python3
"""
Simple launcher for Finance Copilot
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """Main launcher function"""
    print("🚀 Finance Copilot - Simple Launcher")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("💡 Please create a .env file with your API keys:")
        print("   OPENAI_API_KEY=your_openai_key")
        print("   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key")
        print("   PUSHOVER_USER_KEY=your_pushover_user_key")
        print("   PUSHOVER_APP_TOKEN=your_pushover_app_token")
        print("\n📁 You can copy from env_example.txt if it exists")
    
    # Check required environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not set - AI features won't work")
    else:
        print(f"✅ OpenAI API key configured: {openai_key[:10]}...")
    
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not alpha_vantage_key:
        print("⚠️  ALPHA_VANTAGE_API_KEY not set - Market data may be limited")
    else:
        print(f"✅ Alpha Vantage API key configured: {alpha_vantage_key[:10]}...")
    
    pushover_user = os.getenv("PUSHOVER_USER_KEY")
    pushover_token = os.getenv("PUSHOVER_APP_TOKEN")
    if not pushover_user or not pushover_token:
        print("⚠️  Pushover keys not set - Notifications won't work")
    else:
        print(f"✅ Pushover configured: {pushover_user[:10]}... / {pushover_token[:10]}...")
    
    print("\n🚀 Starting Finance Copilot...")
    print("=" * 50)
    
    try:
        # Import and run the main app
        from app import FinanceCopilotApp
        
        print("✅ Finance Copilot app imported successfully")
        print("🌐 App will be available at: http://localhost:7860")
        print("🔑 Login: admin / finance123")
        print("💡 Press Ctrl+C to stop the app")
        
        # Launch the app
        app = FinanceCopilotApp()
        app.launch()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Finance Copilot stopped by user")
        sys.exit(0)
