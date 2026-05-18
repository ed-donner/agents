"""
DuckDuckGo Search MCP Server

Install dependency:  pip install duckduckgo_search
"""

from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS
import json

mcp = FastMCP("search_server")


@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> str:
    """Search the web using DuckDuckGo. Returns titles, URLs and snippets.

    Args:
        query: The search query string
        max_results: Maximum number of results (default 10, max 20)
    """
    max_results = min(max(1, max_results), 20)
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


@mcp.tool()
async def search_news(query: str, max_results: int = 10) -> str:
    """Search recent news articles using DuckDuckGo. Returns titles, URLs, snippets and dates.

    Args:
        query: The news search query
        max_results: Maximum number of results (default 10, max 20)
    """
    max_results = min(max(1, max_results), 20)
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("date", ""),
                    "source": r.get("source", ""),
                })
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


if __name__ == "__main__":
    mcp.run(transport="stdio")
