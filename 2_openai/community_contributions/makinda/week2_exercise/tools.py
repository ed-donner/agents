"""Web search via Serper (Google Search API compatibility for the lab)."""

import os
from typing import Any

import requests
from agents import function_tool


@function_tool
def google_search(query: str) -> str:
    """Search the web with Google (via Serper) and return a short digest of results.

    Use this when you need current facts, statistics, or sources beyond your training data.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return (
            "Search unavailable: SERPER_API_KEY is not set. "
            "Add it to your environment or .env file."
        )

    url = "https://google.serper.dev/search"
    payload: dict[str, Any] = {"q": query, "num": 8}
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Search request failed: {exc}"

    lines: list[str] = [f"Query: {query}\n"]

    for i, item in enumerate(data.get("organic", [])[:6], 1):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        lines.append(f"{i}. {title}\n   {snippet}\n   {link}\n")

    kg = data.get("knowledgeGraph") or {}
    if kg.get("description"):
        lines.append(f"\nKnowledge graph: {kg.get('description', '')}")

    return "\n".join(lines) if len(lines) > 1 else "No organic results returned."
