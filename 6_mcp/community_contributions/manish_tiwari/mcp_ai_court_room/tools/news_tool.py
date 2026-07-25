"""News API helper for legal headlines (optional NEWS_API_KEY)."""

from __future__ import annotations

import os
from typing import Any

import requests


def fetch_news_snippets(query: str, max_items: int = 5) -> list[dict[str, Any]]:
    """Return news article snippets using NewsAPI.org when configured."""
    key = (os.getenv("NEWS_API_KEY") or "").strip()
    if not key:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_items,
        "apiKey": key,
    }
    try:
        resp = requests.get(url, params=params, timeout=25)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []

    out: list[dict[str, Any]] = []
    for art in data.get("articles") or []:
        out.append(
            {
                "title": art.get("title") or "",
                "description": art.get("description") or "",
                "url": art.get("url") or "",
                "source": (art.get("source") or {}).get("name") or "",
            }
        )
    return out
