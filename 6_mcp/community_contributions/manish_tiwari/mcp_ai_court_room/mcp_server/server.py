"""
Courtroom MCP server: exposes search_case and fetch_case_summary over stdio.
Run standalone: python mcp_server/server.py (from project root mcp/)
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP

from tools.case_search_tool import fetch_case_summary_json, search_case_json

mcp = FastMCP("courtroom-legal")


@mcp.tool()
def search_case(query: str | None = None) -> str:
    """
    Search Tavily, SerpAPI, News APIs, and DuckDuckGo for a recent legal case.
    If query is omitted, uses a default that includes today's date for recency.
    Returns JSON with combined_text and source flags.
    """
    return search_case_json(query)


@mcp.tool()
def fetch_case_summary(case_reference: str) -> str:
    """
    Pull a focused summary for a named case, citation fragment, or headline line.
    """
    return fetch_case_summary_json(case_reference)


if __name__ == "__main__":
    mcp.run(transport="stdio")
