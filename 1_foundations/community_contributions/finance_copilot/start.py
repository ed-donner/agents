#!/usr/bin/env python3
"""
Finance Copilot Startup Script
Simple script to start the Finance Copilot application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'gradio',
        'yfinance', 
        'pandas',
        'numpy',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  No .env file found")
        print("Creating .env file from template...")
        
        # Copy env_example.txt to .env
        env_example = Path('env_example.txt')
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual API keys")
            return False
        else:
            print("❌ env_example.txt not found")
            return False
    
    print("✅ .env file found")
    return True

def check_api_keys():
    """Check if required API keys are configured"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_keys = [
        'OPENAI_API_KEY',
        'PUSHOVER_USER_KEY', 
        'PUSHOVER_APP_TOKEN'
    ]
    
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print("⚠️  Missing required API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease add these to your .env file")
        return False
    
    print("✅ All required API keys are configured")
    return True

def run_demo():
    """Run the demo script"""
    print("\n🎬 Running Finance Copilot Demo...")
    try:
        result = subprocess.run([sys.executable, 'demo.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Demo completed successfully")
            return True
        else:
            print(f"❌ Demo failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Demo timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running demo: {str(e)}")
        return False

def start_app():
    """Start the Finance Copilot application"""
    print("\n🚀 Starting Finance Copilot...")
    
    try:
        # Import and start the app
        from app import main
        main()
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Error starting app: {str(e)}")
        return False

def main():
    """Main startup function"""
    print("🚀 Finance Copilot Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check environment file
    if not check_env_file():
        print("\nPlease create and configure your .env file, then run again")
        return
    
    # Check API keys
    if not check_api_keys():
        print("\nPlease configure your API keys in .env file, then run again")
        return
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Run demo (test functionality)")
    print("2. Start web application")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                run_demo()
                break
            elif choice == '2':
                start_app()
                break
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("Please enter 1, 2, or 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()



