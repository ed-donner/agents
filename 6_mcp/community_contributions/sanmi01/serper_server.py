"""
serper_server.py

Exposes a single search tool backed by the Serper API so the agent can
search the web for commodity news and market prices.
"""

import json
import os

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

mcp = FastMCP("serper_server")


@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for news and information using Serper.

    Args:
        query: The search query (e.g. 'maize price Nigeria 2025').
    """
    if not SERPER_API_KEY:
        return "Error: SERPER_API_KEY is not set."

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query}

    try:
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        results = [
            {
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet"),
            }
            for r in data.get("organic", [])[:5]
        ]
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Search failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")