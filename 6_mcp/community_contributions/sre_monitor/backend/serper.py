"""Recent web evidence for the impact verifier, retrieved through Serper."""

import asyncio
import os

import httpx
from langsmith import traceable

from .settings import ssl_context

SERPER_URL = "https://google.serper.dev/search"


def _result(item: dict, source: str) -> dict:
    return {
        "source": source,
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "snippet": item.get("snippet", ""),
        "date": item.get("date"),
    }


async def _search(query: str, source: str, limit: int) -> tuple[list[dict], str | None]:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return [], "SERPER_API_KEY is not configured"
    try:
        async with httpx.AsyncClient(verify=ssl_context(), timeout=30) as client:
            response = await client.post(
                SERPER_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": limit, "tbs": "qdr:d"},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"
    return [_result(item, source) for item in data.get("organic", [])[:limit]], None


@traceable(name="Serper impact verification", run_type="tool")
async def search_incident_evidence(
    service: str, title: str, limit: int = 5
) -> dict:
    """Search the last day of Reddit and the broader web for independent outage reports."""
    reddit_query = (
        f'site:reddit.com "{service}" '
        f'(outage OR down OR incident OR unavailable) ("right now" OR today)'
    )
    web_query = f'"{service}" (outage OR down OR incident) "{title}" today'
    (reddit, reddit_error), (web, web_error) = await asyncio.gather(
        _search(reddit_query, "reddit", limit),
        _search(web_query, "web", limit),
    )
    errors = [error for error in (reddit_error, web_error) if error]
    return {
        "queries": {"reddit": reddit_query, "web": web_query},
        "results": reddit + web,
        "errors": errors,
    }
