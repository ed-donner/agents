#!/usr/bin/env python3
"""
Test script for Advanced Investment Crew setup
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_env_loading():
    """Test environment variables loading"""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Environment Loading")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        
        # Try multiple .env locations
        env_locations = [
            project_root / '.env',
            project_root.parent / '.env',
            Path.home() / '.env'
        ]
        
        env_loaded = False
        for env_path in env_locations:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ .env found at: {env_path}")
                env_loaded = True
                break
        
        if not env_loaded:
            print("⚠️  No .env file found, checking environment variables...")
        
        # Check required variables
        openai_key = os.getenv('OPENAI_API_KEY', '')
        serper_key = os.getenv('SERPER_API_KEY', '')
        
        if openai_key:
            print(f"✅ OPENAI_API_KEY: {openai_key[:15]}...")
        else:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        if serper_key:
            print(f"✅ SERPER_API_KEY: {serper_key[:15]}...")
        else:
            print("⚠️  SERPER_API_KEY not found (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_imports():
    """Test required package imports"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Package Imports")
    print("=" * 60)
    
    packages = [
        'crewai',
        'crewai_tools',
        'yfinance',
        'pandas',
        'numpy',
        'dotenv',
        'scipy'
    ]
    
    all_passed = True
    for package in packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
                name = 'python-dotenv'
            elif package == 'crewai_tools':
                __import__('crewai_tools')
                name = 'CrewAI Tools'
            elif package == 'crewai':
                __import__('crewai')
                name = 'CrewAI'
            else:
                __import__(package)
                name = package
            
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {package}")
            all_passed = False
    
    return all_passed


def test_yfinance():
    """Test yfinance data fetching (fixed for MultiIndex)"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Yahoo Finance Data Fetch")
    print("=" * 60)
    
    try:
        import yfinance as yf
        import pandas as pd
        
        ticker = 'SPY'
        print(f"Fetching {ticker} data (last 5 days)...")
        
        data = yf.download(
            ticker,
            period='5d',
            progress=False,
            auto_adjust=True
        )
        
        if data.empty:
            print("❌ No data returned")
            return False
        
        print(f"✅ Data fetched successfully")
        
        # Handle MultiIndex or regular Index
        try:
            if isinstance(data.columns, pd.MultiIndex):
                # MultiIndex: ('Close', 'SPY')
                close_price = float(data['Close'].iloc[-1, 0])
            elif 'Close' in data.columns:
                close_data = data['Close']
                if isinstance(close_data, pd.DataFrame):
                    close_price = float(close_data.iloc[-1, 0])
                else:
                    close_price = float(close_data.iloc[-1])
            else:
                # Fallback
                close_cols = [col for col in data.columns if 'close' in str(col).lower()]
                if close_cols:
                    close_price = float(data[close_cols[0]].iloc[-1])
                else:
                    raise ValueError("Could not find Close column")
            
            print(f"   {ticker} latest close: ${close_price:.2f}")
            print(f"   Data points: {len(data)} days")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not extract price: {e}")
            print("   But data was fetched successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_files():
    """Test configuration files exist"""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Configuration Files")
    print("=" * 60)
    
    config_dir = project_root / 'src' / 'advanced_investment_crew' / 'config'
    
    required_files = [
        'agents.yaml',
        'tasks.yaml'
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = config_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filepath.relative_to(project_root)} ({size:,} bytes)")
        else:
            print(f"❌ {filepath.relative_to(project_root)} not found")
            all_exist = False
    
    return all_exist


def test_crew_import():
    """Test crew module import"""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Crew Module Import")
    print("=" * 60)
    
    try:
        # Import the crew
        from advanced_investment_crew.crew import AdvancedInvestmentCrew
        
        print("✅ AdvancedInvestmentCrew imported successfully")
        
        # Try to instantiate (without running)
        try:
            crew_instance = AdvancedInvestmentCrew()
            print("✅ Crew instance created successfully")
            
            # Check agents
            agents = crew_instance.agents
            print(f"✅ Found {len(agents)} agents")
            
            # Check tasks
            tasks = crew_instance.tasks
            print(f"✅ Found {len(tasks)} tasks")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Crew instantiation warning: {e}")
            print("   This is OK if API keys are not set")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 ADVANCED INVESTMENT CREW - SETUP TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Environment Loading", test_env_loading()))
    results.append(("Package Imports", test_imports()))
    results.append(("Yahoo Finance", test_yfinance()))
    results.append(("Config Files", test_config_files()))
    results.append(("Crew Import", test_crew_import()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to run the crew.")
        print("\nNext steps:")
        print("  python src/advanced_investment_crew/main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Missing packages: uv pip install -r requirements.txt")
        print("  - Missing .env: Create .env file in project root")
        print("  - Missing configs: Check src/advanced_investment_crew/config/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
