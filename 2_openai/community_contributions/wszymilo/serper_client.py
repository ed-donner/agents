"""
Serper.dev search via shared httpx.AsyncClient (plan.md Phase B).

Lifecycle: one lazy module-level client for all requests. Base URL
`https://google.serper.dev`; endpoint `POST /search`; header `X-API-KEY`.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

_client: httpx.AsyncClient | None = None


def get_serper_async_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url="https://google.serper.dev",
            timeout=httpx.Timeout(30.0),
        )
    return _client


def reset_serper_client_for_tests() -> None:
    """Drop the cached client (tests only; does not aclose)."""
    global _client
    _client = None


def format_serper_organic(data: dict[str, Any]) -> str:
    organic = data.get("organic") or []
    lines: list[str] = []
    for i, item in enumerate(organic[:10], 1):
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        link = item.get("link") or ""
        lines.append(f"{i}. {title}\n{snippet}\n{link}")
    if lines:
        return "\n\n".join(lines)
    return str(data)[:8000]


async def serper_search(query: str) -> str:
    """Run a search and return a plain-text block for the research agent."""
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return "Error: SERPER_API_KEY is not set."
    client = get_serper_async_client()
    try:
        response = await client.post(
            "/search",
            json={"q": query},
            headers={"X-API-KEY": api_key},
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        return f"Search request failed: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Search error: {exc}"
    return format_serper_organic(payload)
