"""News Aggregator Agent - Fetches news from RSS feeds."""

import asyncio
import aiohttp
import feedparser
from typing import Dict, List, Any

from agents import Agent, function_tool


FEEDS = {
    'tech': [
        'https://techcrunch.com/feed/',
        'https://www.theverge.com/rss/index.xml',
        'https://feeds.arstechnica.com/arstechnica/index'
    ],
    'world': [
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml'
    ],
    'business': [
        'http://feeds.bbci.co.uk/news/business/rss.xml',
        'https://www.cnbc.com/id/100003114/device/rss/rss.html'
    ],
    'politics': [
        'https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml',
        'http://feeds.bbci.co.uk/news/politics/rss.xml'
    ],
    'sports': [
        'https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml',
        'http://feeds.bbci.co.uk/sport/rss.xml'
    ]
}


async def fetch_feed(session: aiohttp.ClientSession, url: str) -> List[Dict[str, str]]:
    """Fetch articles from a single RSS feed.
    
    Args:
        session: aiohttp client session
        url: RSS feed URL
        
    Returns:
        List of article dictionaries with title, summary, link, and published date
    """
    try:
        async with session.get(url, timeout=10) as response:
            content = await response.text()
            feed = feedparser.parse(content)
            return [
                {
                    'title': entry.title,
                    'summary': entry.get('summary', ''),
                    'link': entry.link,
                    'published': entry.get('published', '')
                }
                for entry in feed.entries[:3]
            ]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


@function_tool
async def aggregate_news(topic: str, num_sources: int = 5) -> Dict[str, Any]:
    """Aggregate news from RSS feeds concurrently.
    
    Args:
        topic: News topic (tech, world, business, politics, sports)
        num_sources: Number of RSS sources to fetch from
        
    Returns:
        Dictionary containing list of articles
    """
    feed_urls = FEEDS.get(topic, FEEDS['tech'])[:num_sources]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_feed(session, url) for url in feed_urls]
        results = await asyncio.gather(*tasks)
    
    # Flatten results
    articles = [article for feed_articles in results for article in feed_articles]
    
    return {"articles": articles[:15]}


# Create the News Aggregator Agent with Gemini via LiteLLM
NEWS_AGGREGATOR_INSTRUCTIONS = """You are a news aggregator agent. Your task is to fetch and aggregate 
news articles from RSS feeds for a given topic. 

When asked to get news on a topic, use the aggregate_news tool with the topic name 
(tech, world, business, politics, or sports). The tool will fetch articles from multiple sources 
and return a list of the most recent articles."""

news_aggregator_agent = Agent(
    name="News Aggregator",
    instructions=NEWS_AGGREGATOR_INSTRUCTIONS,
    tools=[aggregate_news],
    model="gpt-4o-mini", 
)
