"""Summarizer Agent - Summarizes news articles using Gemini."""

import asyncio
import os
from typing import Dict, List, Any

from openai import OpenAI
from .base import Agent, function_tool


@function_tool
def summarize_articles(articles: List[Dict[str, str]]) -> str:
    """Summarize news articles into a concise 300-word briefing.
    
    Args:
        articles: List of article dictionaries to summarize
        
    Returns:
        Summary text suitable for a 2-minute audio briefing
    """
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_BASE_URL")
    
    if not api_key or not base_url:
        raise ValueError(
            "GEMINI_API_KEY and GEMINI_BASE_URL must be set in environment variables"
        )
    
    if not articles:
        raise ValueError("No articles to summarize")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    context = "\n\n".join([
        f"Article: {a['title']}\n{a['summary']}"
        for a in articles
    ])
    
    prompt = f"""You are a news summarizer. Create a concise, engaging 300-word summary 
    suitable for a 2-minute audio briefing. Structure it as:
    1. Opening hook (1 sentence)
    2. Top 3 stories with key details
    3. Brief closing
    
    Make it conversational and easy to listen to.
    
    Articles:
    {context}
    
    Summary:"""
    
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": "You are a news summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


async def summarize_articles_async(articles: List[Dict[str, str]]) -> str:
    """Async wrapper for summarize_articles to run in executor."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    return await loop.run_in_executor(None, summarize_articles, articles)


# Create the Summarizer Agent
SUMMARIZER_INSTRUCTIONS = """You are a news summarizer agent. Your task is to take a list of news 
articles and create a concise, engaging 300-word summary suitable for a 2-minute audio briefing. 
The summary should have an opening hook, cover the top 3 stories with key details, and include a 
brief closing. Make it conversational and easy to listen to."""

summarizer_agent = Agent(
    name="News Summarizer",
    instructions=SUMMARIZER_INSTRUCTIONS,
    tools=[summarize_articles],
    model="gemini-2.5-flash",
)
