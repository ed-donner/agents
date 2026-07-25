"""Online event discovery via Serper (Google Search API)."""

import os
from datetime import date
from typing import Any

import requests


def search_nairobi_events(query_suffix: str = "") -> str:
    """Search the web for upcoming events in Nairobi."""
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return (
            "Online search unavailable: set SERPER_API_KEY in your environment "
            "or .env file."
        )

    y = date.today().year
    # Bias results toward the current year so Google/Serper return fresher pages.
    q = f"upcoming events Nairobi Kenya {y} {date.today().strftime('%B')} {query_suffix}".strip()
    url = "https://google.serper.dev/search"
    payload: dict[str, Any] = {"q": q, "num": 8}
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return f"Serper search failed: {exc}"

    parts: list[str] = [f"Web search results for: {q}\n"]
    for i, item in enumerate(data.get("organic", [])[:6], 1):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        parts.append(f"{i}. {title}\n   {snippet}\n   {link}\n")

    return "\n".join(parts) if len(parts) > 1 else "No organic search results."
