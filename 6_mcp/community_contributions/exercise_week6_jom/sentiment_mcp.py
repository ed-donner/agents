#!/usr/bin/env python3
"""
Sentiment Analysis MCP Server
Analyzes sentiment for stock tickers using free news APIs and sentiment analysis
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from mcp.server.fastmcp import FastMCP
import asyncio
import json
from transformers import pipeline
import torch

# Initialize MCP server
mcp = FastMCP("sentiment_mcp")

# Configuration
NEWS_API_KEY = os.environ.get("NEWS_API_KEY") 

class TickerInput(BaseModel):
    """Input model for ticker sentiment analysis"""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'TSLA')", min_length=1, max_length=10)
    days_back: Optional[int] = Field(default=7, description="Number of days to look back for news", ge=1, le=30)
    
    @field_validator('ticker')
    @classmethod
    def uppercase_ticker(cls, v):
        return v.upper().strip()

class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    ticker: str
    overall_score: float  # -1 to 1
    sentiment_label: str  # Positive, Negative, Neutral
    summary: str
    article_count: int
    sources: List[Dict[str, Any]]  # Changed to allow mixed types in dict
    analysis_date: str

async def fetch_news_newsapi(ticker: str, days_back: int) -> List[Dict]:
    """Fetch news from NewsAPI.org (free tier allows 100 requests/day)"""
    articles = []
        
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Try multiple query strategies for better results
    queries = [
        f'"{ticker}" stock',  # Exact ticker match with stock keyword
        f'{ticker} company',   # Company name search
        ticker                 # Just the ticker
    ]
    
    async with httpx.AsyncClient() as client:
        for query in queries:
            try:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "from": from_date,
                        "sortBy": "relevancy",
                        "language": "en",
                        "pageSize": 20,
                        "apiKey": NEWS_API_KEY
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("articles"):
                        articles.extend(data["articles"])  # Limit to 10 articles per query
                        break
            except Exception as e:
                print(f"Error fetching news with query '{query}': {e}")
    
    return articles


sentiment_pipeline = None

def init_sentiment_model():
    """Initialize the sentiment analysis model"""
    global sentiment_pipeline
    if sentiment_pipeline is None:
        try:
            # Try to use FinBERT for financial sentiment
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                truncation=True,
                max_length=512,
                device=-1
            )
        except:
            # Fallback to general sentiment model
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                truncation=True,
                max_length=512,
                device=-1
            )
    return sentiment_pipeline

def analyze_sentiment_huggingface(text: str) -> tuple[float, str]:
    """
    Analyze sentiment using Hugging Face transformers
    Returns: (score, label)
    Score: -1 (negative) to 1 (positive)
    """
    try:
        # Initialize model if needed
        analyzer = init_sentiment_model()
                
        # Get prediction
        result = analyzer(text)[0]
        
        # Map the label and score
        label_map = {
            'POSITIVE': 'Positive',
            'positive': 'Positive',
            'NEGATIVE': 'Negative',
            'negative': 'Negative',
            'NEUTRAL': 'Neutral',
            'neutral': 'Neutral',
            'LABEL_1': 'Positive',  # For distilbert
            'LABEL_0': 'Negative',  # For distilbert
        }
        
        label = label_map.get(result['label'], result['label'].capitalize())
        
        # Normalize score to -1 to 1 range
        if label == 'Positive':
            score = result['score']  # 0 to 1
        elif label == 'Negative':
            score = -result['score']  # -1 to 0
        else:  # Neutral
            score = 0.0
        
        return score, label
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        # Fallback to neutral if error
        return 0.0, "Neutral"

def create_summary(ticker: str, articles: List[Dict], sentiment_scores: List[float], sentiment_labels: List[str]) -> str:
    """Create a human-readable summary of the sentiment analysis"""
    if not articles:
        return f"No recent news found for {ticker}. Unable to perform sentiment analysis."
    
    avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    # Count sentiment distribution
    positive_count = sentiment_labels.count("Positive")
    negative_count = sentiment_labels.count("Negative")
    neutral_count = sentiment_labels.count("Neutral")
    
    # Overall sentiment
    if avg_score > 0.15:
        overall = "predominantly positive"
    elif avg_score < -0.15:
        overall = "predominantly negative"
    else:
        overall = "mixed to neutral"
    
    # Find most positive and negative headlines
    if sentiment_scores:
        max_idx = sentiment_scores.index(max(sentiment_scores))
        min_idx = sentiment_scores.index(min(sentiment_scores))
        
        most_positive = articles[max_idx]["title"] if max_idx < len(articles) else ""
        most_negative = articles[min_idx]["title"] if min_idx < len(articles) else ""
    else:
        most_positive = most_negative = ""
    
    summary = f"Sentiment analysis for {ticker} based on {len(articles)} recent articles shows {overall} sentiment "
    summary += f"(score: {avg_score:.2f}). "
    summary += f"Distribution: {positive_count} positive, {negative_count} negative, {neutral_count} neutral. "
    
    if most_positive and sentiment_scores[max_idx] > 0.2:
        summary += f"Most positive: '{most_positive[:100]}...' "
    if most_negative and sentiment_scores[min_idx] < -0.2:
        summary += f"Most concerning: '{most_negative[:100]}...' "
    
    return summary

@mcp.tool(
    name="analyze_ticker_sentiment",
    annotations={
        "title": "Analyze Stock Ticker Sentiment",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def analyze_ticker_sentiment(ticker: str, days_back: int = 7) -> str:
    """
    Analyze sentiment for a given stock ticker based on recent news.
    Returns sentiment score, summary, and source articles.
    """
    params = TickerInput(ticker=ticker, days_back=days_back)

    ticker = params.ticker
    days_back = params.days_back
    
    # Fetch news from multiple sources
    news_articles = await fetch_news_newsapi(ticker, days_back)
    
    # Combine and deduplicate articles
    seen_titles = set()
    unique_articles = []
    
    for article in news_articles:
        title = article.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)
    
    if not unique_articles:
        return json.dumps({
            "ticker": ticker,
            "overall_score": 0.0,
            "sentiment_label": "Unknown",
            "summary": f"No recent news found for {ticker}. Try using a more well-known ticker or check if the ticker is correct.",
            "article_count": 0,
            "sources": [],
            "analysis_date": datetime.now().isoformat()
        }, indent=2)
    
    # Analyze sentiment for each article
    sentiment_scores = []
    sentiment_labels = []
    sources = []
    
    for article in unique_articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        if text.strip():
            score, label = analyze_sentiment_huggingface(text)
            sentiment_scores.append(score)
            sentiment_labels.append(label)
            
            sources.append({
                "title": article.get("title", "")[:200],
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", "") if isinstance(article.get("source"), dict) else article.get("source", ""),
                "sentiment_score": round(score, 3),
                "sentiment_label": label,
                "published": article.get("publishedAt", "")[:10] if article.get("publishedAt") else ""
            })
    
    # Calculate overall sentiment
    if sentiment_scores:
        overall_score = sum(sentiment_scores) / len(sentiment_scores)
        
        if overall_score > 0.1:
            overall_label = "Positive"
        elif overall_score < -0.1:
            overall_label = "Negative"
        else:
            overall_label = "Neutral"
    else:
        overall_score = 0.0
        overall_label = "Unknown"
    
    # Create summary
    summary = create_summary(ticker, unique_articles, sentiment_scores, sentiment_labels)
    
    result = SentimentResult(
        ticker=ticker,
        overall_score=round(overall_score, 3),
        sentiment_label=overall_label,
        summary=summary,
        article_count=len(sources),
        sources=sources[:10],  # Return top 10 sources
        analysis_date=datetime.now().isoformat()
    )
    
    return json.dumps(result.model_dump(), indent=2)

@mcp.tool(
    name="get_sentiment_help",
    annotations={
        "title": "Get Help and Configuration Info",
        "readOnlyHint": True
    }
)
async def get_sentiment_help() -> str:
    """
    Get help information about the sentiment analysis MCP server.
    """
    help_text = """
    Sentiment Analysis MCP Server - Help
    =====================================
    
    This server analyzes market sentiment for stock tickers using news articles.
    
    CONFIGURATION:
    - Set NEWS_API_KEY environment variable for NewsAPI.org (get free key at https://newsapi.org)
    - Without API keys, the server runs in demo mode with sample data
    
    FEATURES:
    - Fetches recent news articles about the ticker
    - Analyzes sentiment using Hugging Face transformers (FinBERT for financial text)
    - Returns overall sentiment score (-1 to 1)
    - Provides sentiment distribution and summary
    - Lists source articles with individual sentiment scores
    
    USAGE:
    Call 'analyze_ticker_sentiment' with:
    - ticker: Stock symbol (e.g., 'AAPL', 'TSLA', 'MSFT')
    - days_back: Number of days to look back (1-30, default: 7)
    
    SENTIMENT SCALE:
    - Score > 0.1: Positive
    - Score < -0.1: Negative
    - -0.1 to 0.1: Neutral
    
    LIMITATIONS:
    - Free tier APIs have rate limits (NewsAPI: 100/day)
    - Sentiment analysis is based on news headlines and descriptions
    - Results depend on news availability for the ticker
    """
    return help_text


if __name__ == "__main__":
    mcp.run(transport='stdio')