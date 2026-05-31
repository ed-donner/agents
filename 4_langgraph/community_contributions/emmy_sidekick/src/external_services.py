"""External service integrations: Tavily web search and YouTube search"""

import requests
from typing import List, Dict, Optional
from tavily import TavilyClient
from src.config import (
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS,
    TAVILY_SEARCH_DEPTH,
    TAVILY_TIMEOUT,
    YOUTUBE_API_KEY,
    YOUTUBE_API_URL,
    YOUTUBE_MAX_RESULTS,
    YOUTUBE_TIMEOUT
)


def search_company_info(company: str, role: str) -> Dict[str, any]:
    """
    Search for company information using Tavily AI search
    
    Args:
        company: Company name
        role: Job role/title
        
    Returns:
        Dictionary with 'content' (combined text) and 'sources' (list of URLs)
        Returns empty content if search fails
    """
    try:
        if not TAVILY_API_KEY:
            return {"content": "", "sources": []}
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Search for company careers, culture, and interview information
        query = f"{company} company culture careers about {role} interview process"
        
        response = client.search(
            query=query,
            max_results=TAVILY_MAX_RESULTS,
            search_depth=TAVILY_SEARCH_DEPTH,
            include_answer=True,  # Get AI-generated summary
            include_raw_content=False  # We'll use the cleaned content
        )
        
        # Combine the answer and results content
        content_parts = []
        sources = []
        
        # Add Tavily's AI answer if available
        if response.get('answer'):
            content_parts.append(response['answer'])
        
        # Add content from each result
        for result in response.get('results', []):
            if result.get('content'):
                content_parts.append(result['content'])
            if result.get('url'):
                sources.append(result['url'])
        
        combined_content = "\n\n".join(content_parts)
        
        return {
            "content": combined_content,
            "sources": sources
        }
        
    except Exception as e:
        print(f"Tavily search error: {e}")
        return {"content": "", "sources": []}


def search_youtube(company: str, role: str) -> List[Dict[str, str]]:
    """
    Search YouTube for interview preparation videos
    
    Args:
        company: Company name
        role: Job role/title
        
    Returns:
        List of video dictionaries with title, url, channel, and thumbnail
    """
    try:
        if not YOUTUBE_API_KEY:
            return []
        
        query = f"{company} {role} interview tips preparation"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': YOUTUBE_MAX_RESULTS,
            'key': YOUTUBE_API_KEY,
            'order': 'relevance'
        }
        
        response = requests.get(YOUTUBE_API_URL, params=params, timeout=YOUTUBE_TIMEOUT)
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            videos.append({
                'title': item['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'channel': item['snippet']['channelTitle'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url']
            })
        
        return videos
        
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []

