"""MCP server exposing Tavily web search (stdio). Launched via uv run from repo root."""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import AsyncTavilyClient

load_dotenv(override=True)

mcp = FastMCP("tavily_search_server")


@mcp.tool()
async def tavily_search(query: str) -> str:
    """Search the web for the given query and return a summary with sources.

    Args:
        query: The search query string.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set."
    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(
        query,
        max_results=5,
        search_depth="basic",
        include_answer=True,
    )

    sections = []
    if response.get("answer"):
        sections.append(f"## Summary\n{response['answer']}")
    if response.get("results"):
        sections.append("## Sources")
        for r in response["results"]:
            sections.append(f"**{r['title']}**\nSource: {r['url']}\n{r['content']}")
    return "\n\n".join(sections) if sections else "No results."


if __name__ == "__main__":
    mcp.run(transport="stdio")
