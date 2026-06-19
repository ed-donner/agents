#!/usr/bin/env python3
"""
Test Alpha Vantage News API to debug source field issue
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_news_api_response():
    """Test the Alpha Vantage News API and see what fields are available"""
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in .env file")
        return
    
    print("🔍 Testing Alpha Vantage News API...")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test with AAPL
    symbol = "AAPL"
    limit = 5
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": api_key,
            "limit": limit
        }
        
        print(f"\n📡 Making request to Alpha Vantage...")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API Response Status: {response.status_code}")
            
            # Check if we have news data
            if "feed" in data:
                news_count = len(data["feed"])
                print(f"📰 Found {news_count} news articles")
                
                if news_count > 0:
                    print(f"\n🔍 First article structure:")
                    first_article = data["feed"][0]
                    
                    # Print all available fields
                    print("Available fields in API response:")
                    for key, value in first_article.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"  {key}: {value[:100]}...")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Check specifically for source field
                    if "source" in first_article:
                        print(f"\n✅ Source field found: '{first_article['source']}'")
                    else:
                        print(f"\n❌ Source field NOT found in API response")
                        
                        # Look for similar fields
                        source_like_fields = [k for k in first_article.keys() if 'source' in k.lower() or 'publisher' in k.lower() or 'author' in k.lower()]
                        if source_like_fields:
                            print(f"🔍 Found similar fields: {source_like_fields}")
                    
                    # Check for time_published field
                    if "time_published" in first_article:
                        print(f"✅ time_published field found: '{first_article['time_published']}'")
                    else:
                        print(f"❌ time_published field NOT found")
                    
                    # Check for overall_sentiment_label field
                    if "overall_sentiment_label" in first_article:
                        print(f"✅ overall_sentiment_label field found: '{first_article['overall_sentiment_label']}'")
                    else:
                        print(f"❌ overall_sentiment_label field NOT found")
                    
                else:
                    print("❌ No news articles found in response")
                    
            else:
                print("❌ No 'feed' key in API response")
                print("Available keys:", list(data.keys()))
                
                # Check for error messages
                if "Error Message" in data:
                    print(f"❌ API Error: {data['Error Message']}")
                if "Note" in data:
                    print(f"⚠️  API Note: {data['Note']}")
                    
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing news API: {e}")
        import traceback
        traceback.print_exc()

def test_market_data_news():
    """Test the market_data.get_company_news method"""
    
    print("\n" + "="*60)
    print("🧪 Testing market_data.get_company_news method...")
    
    try:
        from market_data import MarketDataTool
        
        market_data = MarketDataTool()
        
        # Test the method
        news = market_data.get_company_news("AAPL", 3)
        
        if news:
            print(f"✅ Got {len(news)} news articles")
            
            for i, article in enumerate(news):
                print(f"\n📰 Article {i+1}:")
                print(f"  Title: {article.get('title', 'N/A')}")
                print(f"  Source: {article.get('source', 'N/A')}")
                print(f"  Published: {article.get('published', 'N/A')}")
                print(f"  Sentiment: {article.get('sentiment', 'N/A')}")
                print(f"  URL: {article.get('url', 'N/A')}")
        else:
            print("❌ No news returned from market_data method")
            
    except Exception as e:
        print(f"❌ Error testing market_data method: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test runner"""
    print("🚀 Alpha Vantage News API Debug Test")
    print("=" * 60)
    
    # Test 1: Direct API response
    test_news_api_response()
    
    # Test 2: Market data method
    test_market_data_news()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    print("This test helps identify:")
    print("1. What fields are actually available in the API response")
    print("2. Whether the source field exists or has a different name")
    print("3. If the market_data method is correctly extracting fields")
    print("4. Any API errors or rate limiting issues")

if __name__ == "__main__":
    main()
