"""Local DuckDuckGo text search over MCP stdio (no npm server, no stdout spam)."""

from typing import Any

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ddg_search_server")


@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search the web via DuckDuckGo. Returns title, url, and snippet per result. No API key."""
    max_results = min(max(1, max_results), 20)
    results: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for row in ddgs.text(query, max_results=max_results):
                if row.get("title") and row.get("href"):
                    results.append(
                        {
                            "title": row.get("title", ""),
                            "url": row.get("href", ""),
                            "snippet": row.get("body", row.get("snippet", "")),
                        }
                    )
        return results
    except RatelimitException as e:
        return [{"title": "Error", "url": "", "snippet": f"Rate limited: {e}"}]
    except TimeoutException as e:
        return [{"title": "Error", "url": "", "snippet": f"Timeout: {e}"}]
    except DDGSException as e:
        return [{"title": "Error", "url": "", "snippet": f"Search error: {e}"}]
    except Exception as e:
        return [{"title": "Error", "url": "", "snippet": f"Unexpected error: {e}"}]


if __name__ == "__main__":
    mcp.run(transport="stdio")
