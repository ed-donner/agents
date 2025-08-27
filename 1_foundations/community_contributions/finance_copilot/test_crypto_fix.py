#!/usr/bin/env python3
"""
Test Crypto Price Fix for Finance Copilot
Verify that crypto prices are now correct and symbol resolution works
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_crypto_symbol_resolution():
    """Test that crypto symbols are properly resolved"""
    print("🔍 Testing Crypto Symbol Resolution...")
    
    try:
        from market_data import MarketDataTool
        
        tool = MarketDataTool()
        
        # Test common crypto symbols
        test_cases = [
            ('BTC', 'BTC-USD'),
            ('ETH', 'ETH-USD'),
            ('ADA', 'ADA-USD'),
            ('SOL', 'SOL-USD'),
            ('BTC-USD', 'BTC-USD'),  # Already correct format
            ('ETH-USD', 'ETH-USD')   # Already correct format
        ]
        
        print("🔍 Testing symbol resolution...")
        for input_symbol, expected_resolved in test_cases:
            resolved = tool._resolve_crypto_symbol(input_symbol)
            status = "✅" if resolved == expected_resolved else "❌"
            print(f"   {status} {input_symbol} → {resolved} (expected: {expected_resolved})")
            
            if resolved != expected_resolved:
                return False
        
        print("✅ All symbol resolutions working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Symbol resolution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crypto_prices():
    """Test that crypto prices are now correct"""
    print("\n" + "="*60)
    print("💰 Testing Crypto Prices...")
    
    try:
        from market_data import MarketDataTool
        
        tool = MarketDataTool()
        
        # Test BTC price (should be over $100k)
        print("🔍 Testing BTC price...")
        btc_result = tool.get_crypto_price('BTC')
        
        if "error" in btc_result:
            print(f"❌ BTC price failed: {btc_result['error']}")
            return False
        
        btc_price = btc_result['price']
        print(f"   BTC Price: ${btc_price:,.2f}")
        
        # Check if price is reasonable (should be over $100k)
        if btc_price < 100000:
            print(f"❌ BTC price too low: ${btc_price:,.2f} (expected > $100,000)")
            return False
        
        print("✅ BTC price is correct (> $100k)")
        
        # Test ETH price (should be over $1k)
        print("\n🔍 Testing ETH price...")
        eth_result = tool.get_crypto_price('ETH')
        
        if "error" in eth_result:
            print(f"❌ ETH price failed: {eth_result['error']}")
            return False
        
        eth_price = eth_result['price']
        print(f"   ETH Price: ${eth_price:,.2f}")
        
        # Check if price is reasonable (should be over $1k)
        if eth_price < 1000:
            print(f"❌ ETH price too low: ${eth_price:,.2f} (expected > $1,000)")
            return False
        
        print("✅ ETH price is correct (> $1k)")
        
        return True
        
    except Exception as e:
        print(f"❌ Crypto prices test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_symbol_auto_resolution():
    """Test that the app automatically resolves symbols correctly"""
    print("\n" + "="*60)
    print("🤖 Testing App Symbol Auto-Resolution...")
    
    try:
        from app import FinanceCopilotApp
        
        app = FinanceCopilotApp()
        
        # Test that BTC resolves to BTC-USD in the app
        print("🔍 Testing BTC symbol in app...")
        crypto_data = app.get_crypto_data('BTC')
        
        if "BTC-USD" in crypto_data and "111" in crypto_data:
            print("✅ App correctly resolves BTC to BTC-USD with correct price")
            return True
        else:
            print("❌ App not resolving BTC correctly")
            print(f"Result: {crypto_data[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ App symbol resolution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_clearing():
    """Test that cache clearing works properly"""
    print("\n" + "="*60)
    print("🧹 Testing Cache Clearing...")
    
    try:
        from market_data import MarketDataTool
        
        tool = MarketDataTool()
        
        # Add some data to cache
        tool._cache_data('TEST', {'test': 'data'})
        print("   Added test data to cache")
        
        # Clear cache
        tool.clear_cache()
        print("   Cache cleared")
        
        # Check if cache is empty
        if len(tool.cache) == 0:
            print("✅ Cache cleared successfully")
            return True
        else:
            print(f"❌ Cache not cleared: {len(tool.cache)} items remaining")
            return False
        
    except Exception as e:
        print(f"❌ Cache clearing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - Crypto Price Fix Test")
    print("=" * 60)
    
    # Test 1: Symbol resolution
    symbol_test = test_crypto_symbol_resolution()
    
    # Test 2: Crypto prices
    price_test = test_crypto_prices()
    
    # Test 3: App symbol resolution
    app_test = test_symbol_auto_resolution()
    
    # Test 4: Cache clearing
    cache_test = test_cache_clearing()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if symbol_test and price_test and app_test and cache_test:
        print("✅ All tests passed! Crypto price issue is completely resolved.")
        print("\n🎉 What's been verified:")
        print("   - Crypto symbols are automatically resolved correctly")
        print("   - BTC price shows correct value (> $100k)")
        print("   - ETH price shows correct value (> $1k)")
        print("   - App automatically resolves symbols")
        print("   - Cache clearing works properly")
        
        print("\n🌐 To test in the UI:")
        print("   1. Go to the Market Data tab")
        print("   2. Enter: 'BTC' (not BTC-USD)")
        print("   3. Click: 'Get Crypto Data'")
        print("   4. Should show: BTC-USD with price > $100k")
        
        print("\n💡 Key improvements:")
        print("   - Smart symbol resolution (BTC → BTC-USD)")
        print("   - Correct cryptocurrency data (not ETF data)")
        print("   - Real-time prices from Yahoo Finance")
        print("   - Helpful error messages and guidance")
        
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
        if not symbol_test:
            print("\n💡 Symbol resolution may have issues")
        
        if not price_test:
            print("\n💡 Crypto prices may still be incorrect")
        
        if not app_test:
            print("\n💡 App integration may have problems")
        
        if not cache_test:
            print("\n💡 Cache management may not be working")
    
    return symbol_test and price_test and app_test and cache_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
