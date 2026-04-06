"""Research tool using Tavily search API."""

from tavily import TavilyClient
from config import config


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web via Tavily. Returns list of {title, url, content}.
    Raises RuntimeError if TAVILY_API_KEY is not configured.
    """
    if not config.TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set. Add it to your .env file.")

    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    response = client.search(query=query, max_results=max_results)

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:1000],
        }
        for r in response.get("results", [])
    ]
