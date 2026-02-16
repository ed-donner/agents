#!/usr/bin/env python3
"""
Environment Variable Checker for Finance Copilot
This script helps debug environment variable configuration issues
"""

import os
from dotenv import load_dotenv

def check_env():
    """Check all environment variables for Finance Copilot"""
    print("🔍 Finance Copilot Environment Variable Checker")
    print("=" * 60)
    
    # Load .env file
    print("📁 Loading .env file...")
    load_dotenv()
    
    # Required variables
    required_vars = {
        "GOOGLE_CLIENT_ID": "Google OAuth Client ID (required for authentication)",
        "GOOGLE_CLIENT_SECRET": "Google OAuth Client Secret (required for authentication)",
    }
    
    # Optional but recommended variables
    optional_vars = {
        "OPENAI_API_KEY": "OpenAI API Key (required for AI features)",
        "ALPHA_VANTAGE_API_KEY": "Alpha Vantage API Key (required for market data)",
        "PUSHOVER_USER_KEY": "Pushover User Key (required for notifications)",
        "PUSHOVER_APP_TOKEN": "Pushover App Token (required for notifications)",
        "SECRET_KEY": "Secret key for sessions (auto-generated if not set)",
    }
    
    # Check required variables
    print("\n🔴 REQUIRED Variables:")
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}... ({description})")
        else:
            print(f"❌ {var}: Missing ({description})")
            missing_required.append(var)
    
    # Check optional variables
    print("\n🟡 OPTIONAL Variables:")
    missing_optional = []
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if var == "SECRET_KEY" and value == "your_secret_key_change_this":
                print(f"⚠️  {var}: Using default value - {description}")
            else:
                print(f"✅ {var}: {value[:10]}... ({description})")
        else:
            if var == "SECRET_KEY":
                print(f"ℹ️  {var}: Will auto-generate ({description})")
            else:
                print(f"❌ {var}: Missing ({description})")
                missing_optional.append(var)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    if not missing_required:
        print("✅ All REQUIRED variables are set!")
    else:
        print(f"❌ Missing {len(missing_required)} REQUIRED variables:")
        for var in missing_required:
            print(f"   • {var}")
    
    if missing_optional:
        print(f"\n⚠️  Missing {len(missing_optional)} OPTIONAL variables:")
        for var in missing_optional:
            print(f"   • {var}")
        print("\n💡 These are not required to run the app, but some features may not work.")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if missing_required:
        print("1. Set all REQUIRED variables in your .env file")
        print("2. Make sure the .env file is in the same directory as this script")
        print("3. Restart the application after setting variables")
    
    if "OPENAI_API_KEY" in missing_optional:
        print("4. Set OPENAI_API_KEY for AI Assistant features")
    
    if "ALPHA_VANTAGE_API_KEY" in missing_optional:
        print("5. Set ALPHA_VANTAGE_API_KEY for market data")
    
    if "PUSHOVER_USER_KEY" in missing_optional or "PUSHOVER_APP_TOKEN" in missing_optional:
        print("6. Set Pushover keys for notifications")
    
    # Check .env file location
    print("\n📁 .env File Location:")
    env_file = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_file):
        print(f"✅ .env file found at: {env_file}")
        # Check file size
        size = os.path.getsize(env_file)
        print(f"   File size: {size} bytes")
        
        # Show first few lines (without sensitive data)
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
                print(f"   Number of lines: {len(lines)}")
                print("   First few lines:")
                for i, line in enumerate(lines[:5]):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'OPENAI_API_KEY']:
                            print(f"     {key}=***{value[-4:] if len(value) > 4 else '***'}")
                        else:
                            print(f"     {line.strip()}")
                    else:
                        print(f"     {line.strip()}")
        except Exception as e:
            print(f"   Error reading file: {e}")
    else:
        print(f"❌ .env file not found at: {env_file}")
        print("   Please create a .env file in the current directory")
    
    return len(missing_required) == 0

if __name__ == "__main__":
    success = check_env()
    if success:
        print("\n🎉 Environment check passed! You can now run the OAuth app.")
        print("   python3 run_working_oauth.py")
    else:
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
