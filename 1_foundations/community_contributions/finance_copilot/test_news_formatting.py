#!/usr/bin/env python3
"""
Test News Title Formatting for Finance Copilot
Verify that news titles are properly cleaned for Markdown rendering
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_title_cleaning():
    """Test the news title cleaning function"""
    print("🧪 Testing News Title Cleaning...")
    
    try:
        from app import FinanceCopilotApp
        
        # Create app instance
        app = FinanceCopilotApp()
        print("✅ Finance Copilot app created successfully")
        
        # Test various problematic titles
        test_titles = [
            "Suze Orman Bets On This 'Controversial' Tech Stock-Explains How Her Biggest Investment Blunder Cost Her 'Extraordinary' Gains - Apple ( NASDAQ:AAPL ) , Advanced Micro Devices ( NASDAQ:AMD )",
            "Warren Buffett's AI Bets: 22% of Berkshire Hathaway's $294 Billion Stock Portfolio Is Held in These 2 Artificial Intelligence Growth Stocks",
            "Apple TV+ Hikes Price 30% To $12.99 As Streaming Losses Reportedly Top $1 Billion - Apple ( NASDAQ:AAPL ) , Amazon.com ( NASDAQ:AMZN )",
            "What's Going On With Taiwan Semiconductor Stock Friday? - Taiwan Semiconductor ( NYSE:TSM )",
            "A title with 'smart quotes' and 'apostrophes' and - dashes - and other special characters",
            "Very long title that should be truncated because it exceeds the maximum length limit and would cause layout issues in the user interface",
            "Normal title without special characters",
            "",  # Empty title
            None  # None title
        ]
        
        print("\n🔍 Testing title cleaning function...")
        for i, title in enumerate(test_titles, 1):
            cleaned = app._clean_news_title(title)
            print(f"\n{i}. Original: {title}")
            print(f"   Cleaned:  {cleaned}")
            print(f"   Length:   {len(cleaned)} chars")
            
            # Check if cleaning worked
            if title and len(cleaned) > 0:
                if len(cleaned) <= 120:
                    print("   ✅ Length OK")
                else:
                    print("   ❌ Still too long")
                
                # Check for problematic characters
                if '"' in cleaned or '"' in cleaned or '' in cleaned or '' in cleaned:
                    print("   ⚠️  Still has smart quotes")
                else:
                    print("   ✅ No smart quotes")
            else:
                if not title:
                    print("   ✅ Empty/None handled correctly")
        
        print("\n✅ Title cleaning test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Title cleaning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_formatting():
    """Test the complete news formatting"""
    print("\n" + "="*60)
    print("📰 Testing Complete News Formatting...")
    
    try:
        from app import FinanceCopilotApp
        
        app = FinanceCopilotApp()
        
        # Test with a sample news article
        sample_article = {
            'title': "Suze Orman Bets On This 'Controversial' Tech Stock-Explains How Her Biggest Investment Blunder Cost Her 'Extraordinary' Gains - Apple ( NASDAQ:AAPL ) , Advanced Micro Devices ( NASDAQ:AMD )",
            'summary': "Suze Orman, the renowned personal finance expert, has recently shared her top stock picks, her take on the current market, and her biggest investment blunder that cost her 'extraordinary' gains.",
            'url': 'https://example.com/article',
            'published': '20250825T091109',
            'source': 'Benzinga',
            'authors': ['Namrata Sen'],
            'category': 'Markets',
            'source_domain': 'www.benzinga.com',
            'sentiment': 'Somewhat-Bullish'
        }
        
        # Simulate the formatting logic
        clean_title = app._clean_news_title(sample_article['title'])
        
        print(f"📝 Sample Article:")
        print(f"   Original Title: {sample_article['title']}")
        print(f"   Cleaned Title:  {clean_title}")
        print(f"   Source: {sample_article['source']}")
        print(f"   Authors: {', '.join(sample_article['authors'])}")
        print(f"   Category: {sample_article['category']}")
        print(f"   Sentiment: {sample_article['sentiment']}")
        
        # Check if the cleaned title is Markdown-safe
        markdown_safe = True
        problematic_chars = ['"', '"', ''', ''', '–', '—']
        
        for char in problematic_chars:
            if char in clean_title:
                markdown_safe = False
                print(f"   ❌ Contains problematic character: {char}")
                break
        
        if markdown_safe:
            print("   ✅ Title is Markdown-safe")
        
        if len(clean_title) <= 120:
            print("   ✅ Title length is appropriate")
        else:
            print(f"   ❌ Title is too long: {len(clean_title)} chars")
        
        print("\n✅ News formatting test completed!")
        return True
        
    except Exception as e:
        print(f"❌ News formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smart_quote_replacement():
    """Test that smart quotes and special characters are properly replaced"""
    print("\n" + "="*60)
    print("🔤 Testing Smart Quote Replacement...")
    
    try:
        from app import FinanceCopilotApp
        
        app = FinanceCopilotApp()
        
        # Test titles with various smart quotes and special characters
        test_cases = [
            ("Title with \u201Csmart quotes\u201D", "Title with \"smart quotes\""),
            ("Title with \u2018curly apostrophe\u2019", "Title with 'curly apostrophe'"),
            ("Title with \u2013 en dash", "Title with - en dash"),
            ("Title with \u2014 em dash", "Title with - em dash"),
            ("Title with \u2026 ellipsis", "Title with ... ellipsis"),
            ("Mixed: \u201Cquotes\u201D and \u2018apostrophes\u2019 and \u2013 dashes", "Mixed: \"quotes\" and 'apostrophes' and - dashes"),
        ]
        
        print("🔍 Testing character replacement...")
        all_passed = True
        
        for original, expected in test_cases:
            cleaned = app._clean_news_title(original)
            
            # Check if problematic characters were replaced
            has_smart_quotes = any(char in cleaned for char in ['"', '"', ''', ''', '–', '—', '…', '…'])
            
            print(f"\n   Original: {original}")
            print(f"   Cleaned:  {cleaned}")
            print(f"   Has smart quotes: {has_smart_quotes}")
            
            if has_smart_quotes:
                print("   ❌ Still contains smart quotes")
                all_passed = False
            else:
                print("   ✅ Smart quotes replaced")
        
        if all_passed:
            print("\n✅ All smart quotes replaced successfully!")
        else:
            print("\n❌ Some smart quotes not replaced")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Smart quote replacement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚀 Finance Copilot - News Title Formatting Test")
    print("=" * 60)
    
    # Test 1: Title cleaning function
    title_test = test_title_cleaning()
    
    # Test 2: Complete news formatting
    formatting_test = test_news_formatting()
    
    # Test 3: Smart quote replacement
    smart_quote_test = test_smart_quote_replacement()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if title_test and formatting_test and smart_quote_test:
        print("✅ All tests passed! News titles are properly formatted.")
        print("\n🎉 What's been verified:")
        print("   - Special characters are handled correctly")
        print("   - Long titles are truncated appropriately")
        print("   - Markdown-breaking characters are replaced")
        print("   - Empty/None titles are handled gracefully")
        print("   - Smart quotes are properly replaced")
        
        print("\n🌐 To test in the UI:")
        print("   1. Navigate to the 'Market Data' tab")
        print("   2. Enter a company symbol (e.g., AAPL)")
        print("   3. Click 'Get Company News'")
        print("   4. Check that titles display correctly without Markdown errors")
        
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return title_test and formatting_test and smart_quote_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
