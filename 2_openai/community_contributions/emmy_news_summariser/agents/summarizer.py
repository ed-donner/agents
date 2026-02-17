"""Summarizer Agent - Summarizes news articles using OpenAI."""

import os
import json
from typing import Dict, List, Any

from agents import Agent, function_tool
from openai import OpenAI


@function_tool
def summarize_articles(articles_json: str) -> str:
    """Summarize news articles into a concise 300-word briefing.
    
    Args:
        articles_json: JSON string containing list of article dictionaries to summarize
        
    Returns:
        Summary text suitable for a 2-minute audio briefing
    """
    # Parse JSON string to list
    try:
        articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format for articles")
    
    if not articles:
        raise ValueError("No articles to summarize")
    
    context = "\n\n".join([
        f"Article: {a.get('title', 'No title')}\n{a.get('summary', '')}"
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
    
    # Use OpenAI API directly
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set in environment variables")
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a news summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


# Create the Summarizer Agent
SUMMARIZER_INSTRUCTIONS = """You are a news summarizer agent. Your task is to take a list of news 
articles and create a concise, engaging 300-word summary suitable for a 2-minute audio briefing. 

When given articles, use the summarize_articles tool with the articles in JSON format.
The summary should have an opening hook, cover the top 3 stories with key details, and include a 
brief closing. Make it conversational and easy to listen to."""

summarizer_agent = Agent(
    name="News Summarizer",
    instructions=SUMMARIZER_INSTRUCTIONS,
    tools=[summarize_articles],
    model="gpt-4o-mini",  
)
