from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("market_sentiment")

# Browser management
_browser = None
_context = None


async def get_browser():
    """Get or create browser instance"""
    global _browser, _context
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(headless=True)
        _context = await _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    return _context


def analyze_sentiment(text: str) -> str:
    """Simple keyword-based sentiment analysis"""
    text_lower = text.lower()
    
    positive = ['surge', 'gain', 'rally', 'rise', 'bullish', 'profit', 'growth',
                'beat', 'strong', 'up', 'higher', 'soar', 'jump', 'outperform']
    
    negative = ['fall', 'drop', 'plunge', 'crash', 'bearish', 'loss', 'decline',
                'miss', 'weak', 'down', 'lower', 'sink', 'tumble', 'underperform']
    
    pos_count = sum(1 for word in positive if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    
    if pos_count > neg_count * 1.5:
        return "BULLISH"
    elif neg_count > pos_count * 1.5:
        return "BEARISH"
    return "NEUTRAL"


@mcp.tool()
async def get_stock_sentiment(symbol: str) -> str:
    """Analyze sentiment for a specific stock from recent news.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
    """
    try:
        context = await get_browser()
        page = await context.new_page()
        
        # Search news
        query = f"{symbol} stock news latest".replace(' ', '+')
        await page.goto(f"https://www.google.com/search?q={query}&tbm=nws")
        await page.wait_for_timeout(2000)
        
        # Extract headlines - try multiple selectors for robustness
        headlines = []
        selectors = ["div.SoaBEf", "div.n0jPhd", "article h3", "div[role='article']"]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if len(elements) > 5:  # Found meaningful results
                for element in elements[:10]:
                    try:
                        text = await element.inner_text()
                        if text and len(text) > 10:
                            headlines.append(text.strip())
                    except:
                        continue
                if headlines:
                    break
        
        await page.close()
        
        if not headlines:
            return f"{symbol}: No recent news (NEUTRAL)"
        
        # Analyze each headline once
        sentiments = [analyze_sentiment(h) for h in headlines]
        
        bullish = sentiments.count("BULLISH")
        bearish = sentiments.count("BEARISH")
        
        # Determine overall sentiment from counts
        if bullish > bearish * 1.5:
            sentiment = "BULLISH"
        elif bearish > bullish * 1.5:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        result = f"{symbol} Sentiment: {sentiment} ({bullish} bullish, {bearish} bearish signals)\n\n"
        result += "Recent Headlines:\n"
        result += "\n".join([f"- {h[:100]}" for h in headlines[:5]])
        
        return result
        
    except Exception as e:
        return f"Error analyzing {symbol}: {str(e)}"


@mcp.tool()
async def get_market_news(topic: str) -> str:
    """Get latest financial news on any topic.
    
    Args:
        topic: Topic to search (e.g., 'tech stocks', 'interest rates')
    """
    try:
        context = await get_browser()
        page = await context.new_page()
        
        # Search news
        query = f"{topic} financial news".replace(' ', '+')
        await page.goto(f"https://www.google.com/search?q={query}&tbm=nws")
        await page.wait_for_timeout(2000)
        
        # Extract news - try multiple selectors
        news_items = []
        selectors = ["div.SoaBEf", "div.n0jPhd", "article h3", "div[role='article']"]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if len(elements) > 5:
                for element in elements[:8]:
                    try:
                        text = await element.inner_text()
                        if text and len(text) > 20:
                            news_items.append(text.strip())
                    except:
                        continue
                if news_items:
                    break
        
        await page.close()
        
        if not news_items:
            return f"No news found for: {topic}"
        
        result = f"Latest News: {topic}\n\n"
        result += "\n".join([f"{i+1}. {item[:150]}" for i, item in enumerate(news_items[:6])])
        
        return result
        
    except Exception as e:
        return f"Error fetching news for {topic}: {str(e)}"


@mcp.tool()
async def analyze_overall_sentiment() -> str:
    """Analyze overall market sentiment (fear/greed indicator)."""
    try:
        context = await get_browser()
        page = await context.new_page()
        
        # Get general market news
        await page.goto("https://www.google.com/search?q=stock+market+news+today&tbm=nws")
        await page.wait_for_timeout(2000)
        
        # Extract headlines - try multiple selectors
        headlines = []
        selectors = ["div.SoaBEf", "div.n0jPhd", "article h3", "div[role='article']"]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if len(elements) > 8:
                for element in elements[:15]:
                    try:
                        text = await element.inner_text()
                        if text and len(text) > 10:
                            headlines.append(text.strip())
                    except:
                        continue
                if headlines:
                    break
        
        await page.close()
        
        if not headlines:
            return "Unable to determine market sentiment"
        
        # Analyze each headline once
        sentiments = [analyze_sentiment(h) for h in headlines]
        
        bullish = sentiments.count("BULLISH")
        bearish = sentiments.count("BEARISH")
        neutral = sentiments.count("NEUTRAL")
        
        # Determine mood
        if bullish > bearish * 1.5:
            mood = "GREEDY (Risk-On)"
        elif bearish > bullish * 1.5:
            mood = "FEARFUL (Risk-Off)"
        else:
            mood = "NEUTRAL (Cautious)"
        
        result = f"Overall Market Sentiment: {mood}\n\n"
        result += f"Signals: {bullish} bullish, {bearish} bearish, {neutral} neutral\n\n"
        result += "Top Headlines:\n"
        result += "\n".join([f"- {h[:100]}" for h in headlines[:5]])
        result += f"\n\nAssessment: {bullish*100//len(headlines)}% bullish signals"
        
        return result
        
    except Exception as e:
        return f"Error analyzing market sentiment: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
