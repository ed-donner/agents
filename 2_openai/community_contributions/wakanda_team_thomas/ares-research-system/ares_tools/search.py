"""Tavily web search tool for the ARES Web Specialist agent."""

from __future__ import annotations

import os

from agents import function_tool
from tavily import TavilyClient


def get_travily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY environment variable is not set")
    return TavilyClient(api_key=api_key)


@function_tool
def travily_web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily and return extracted content.
    Args:
        query: The search query to execute.
        max_results: Maximum number of results to return (1-10).
    """
    client = get_travily_client()
    response = client.search(
        query=query,
        max_results=min(max_results, 10),
        include_answer=True,
    )
    # Format results for the agent
    parts: list[str] = []
    if response.get("answer"):
        parts.append(f"## AI Summary\n{response['answer']}\n")

    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        parts.append(f"### [{i}] {title}\n**URL:** {url}\n{content}\n")

    return "\n".join(parts) if parts else "No results found."
