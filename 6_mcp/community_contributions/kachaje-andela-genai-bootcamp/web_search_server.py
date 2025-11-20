from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
from typing import List, Dict
from pydantic import BaseModel, Field
from local_trace import span

mcp = FastMCP("web_search_server")


class SearchResult(BaseModel):
    """A single web search result."""
    title: str = Field(description="The title of the search result")
    url: str = Field(description="The URL of the search result")
    snippet: str = Field(description="A brief snippet or description of the result")


@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search the web for information using DuckDuckGo.
    
    This tool performs web searches and returns results with titles, URLs, and snippets.
    It works entirely locally without requiring any API keys.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10, max: 20)
    
    Returns:
        A list of search results, each containing 'title', 'url', and 'snippet' keys
    """
    # Limit max_results to a reasonable range
    max_results = min(max(1, max_results), 20)
    
    with span("web_search", attributes={
        "query": query,
        "max_results": max_results,
        "server": "web_search_server"
    }) as search_span:
        results = []
        
        try:
            with span("duckduckgo_search", attributes={"query": query, "max_results": max_results}):
                with DDGS() as ddgs:
                    for result in ddgs.text(query, max_results=max_results):
                        if result.get("title") and result.get("href"):
                            results.append({
                                "title": result.get("title", ""),
                                "url": result.get("href", ""),
                                "snippet": result.get("body", result.get("snippet", ""))
                            })
            
            search_span.attributes["result_count"] = len(results)
            return results
        
        except RatelimitException as e:
            error_msg = str(e)
            with span("search_error", attributes={
                "error_type": "RatelimitException",
                "error_message": error_msg,
                "is_rate_limit": True
            }):
                search_span.attributes["result_count"] = 0
                return [{
                    "title": "Error",
                    "url": "",
                    "snippet": f"Rate limit exceeded. Please try again later. Error: {error_msg}"
                }]
        
        except TimeoutException as e:
            error_msg = str(e)
            with span("search_error", attributes={
                "error_type": "TimeoutException",
                "error_message": error_msg
            }):
                search_span.attributes["result_count"] = 0
                return [{
                    "title": "Error",
                    "url": "",
                    "snippet": f"Search request timed out. Please try again. Error: {error_msg}"
                }]
        
        except DDGSException as e:
            error_msg = str(e)
            with span("search_error", attributes={
                "error_type": "DDGSException",
                "error_message": error_msg
            }):
                search_span.attributes["result_count"] = 0
                return [{
                    "title": "Error",
                    "url": "",
                    "snippet": f"Search error: {error_msg}"
                }]
        
        except Exception as e:
            error_msg = str(e)
            with span("unexpected_error", attributes={
                "error_type": type(e).__name__,
                "error_message": error_msg
            }):
                search_span.attributes["result_count"] = 0
                return [{
                    "title": "Error",
                    "url": "",
                    "snippet": f"Unexpected error during search: {error_msg}"
                }]


if __name__ == "__main__":
    mcp.run(transport='stdio')

