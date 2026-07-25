"""Aggregate legal case discovery: Tavily, SerpAPI, News, DuckDuckGo fallback."""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

import requests
from rich.console import Console

from tools.news_tool import fetch_news_snippets

console = Console()


def default_latest_legal_search_query() -> str:
    """Recency-focused query using today's date (for news / web filtering)."""
    today = date.today()
    iso = today.isoformat()
    long_fmt = today.strftime("%B %d, %Y")
    month_year = today.strftime("%B %Y")
    return (
        f"latest legal case court litigation judgment appellate ruling news "
        f'{long_fmt} {iso} {month_year} {today.year} breaking'
    )


def _tavily_search(query: str) -> dict[str, Any]:
    key = (
        os.getenv("TAVILY_API_KEY") or os.getenv("TRAVILY_API_KEY") or ""
    ).strip()
    if not key:
        return {"error": "TAVILY_API_KEY not set", "results": []}
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=key)
        return client.search(query=query, search_depth="advanced", max_results=8)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]Tavily search failed:[/yellow] {exc}")
        return {"error": str(exc), "results": []}


def _serpapi_search(query: str) -> dict[str, Any]:
    key = (os.getenv("SERPAPI_API_KEY") or os.getenv("SERPER_API_KEY") or "").strip()
    if not key:
        return {"organic_results": [], "skipped": "no SerpAPI key"}
    try:
        resp = requests.get(
            "https://serpapi.com/search.json",
            params={"q": query, "api_key": key, "num": 8},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        console.print(f"[yellow]SerpAPI search failed:[/yellow] {exc}")
        return {"organic_results": [], "error": str(exc)}


def _duckduckgo_search(query: str) -> list[dict[str, str]]:
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=8))
        return results
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]DuckDuckGo search failed:[/yellow] {exc}")
        return []


def _format_tavily(raw: dict[str, Any]) -> str:
    lines: list[str] = []
    for item in raw.get("results") or []:
        title = item.get("title") or ""
        content = item.get("content") or item.get("snippet") or ""
        url = item.get("url") or ""
        lines.append(f"- {title}\n  {content}\n  {url}")
    return "\n".join(lines) if lines else ""


def _format_serp(raw: dict[str, Any]) -> str:
    lines: list[str] = []
    for item in raw.get("organic_results") or []:
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        link = item.get("link") or ""
        lines.append(f"- {title}\n  {snippet}\n  {link}")
    return "\n".join(lines) if lines else ""


def _format_ddg(items: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for item in items:
        title = item.get("title") or ""
        body = item.get("body") or ""
        href = item.get("href") or ""
        lines.append(f"- {title}\n  {body}\n  {href}")
    return "\n".join(lines) if lines else ""


def search_case(query: str | None = None) -> dict[str, Any]:
    """
    Search multiple sources for a recent legal matter.
    Default query includes today's date to bias toward current stories.
    """
    q = (query or default_latest_legal_search_query()).strip()
    tavily_raw = _tavily_search(q)
    serp_raw = _serpapi_search(f"{q} court judgment case law litigation")
    ddg_raw = _duckduckgo_search(q)

    news = fetch_news_snippets(f"{q} legal court {date.today().strftime('%Y-%m')}")

    news_block = "\n".join(
        f"- {n['title']}: {n['description']} ({n['url']})" for n in news
    )

    combined_text = "\n\n--- TAVILY ---\n"
    combined_text += _format_tavily(tavily_raw) or "(no Tavily results)"
    combined_text += "\n\n--- SERP ---\n"
    combined_text += _format_serp(serp_raw) or "(no SerpAPI results)"
    combined_text += "\n\n--- DUCKDUCKGO ---\n"
    combined_text += _format_ddg(ddg_raw) or "(no DDG results)"
    combined_text += "\n\n--- NEWS ---\n"
    combined_text += news_block or "(no News API results)"

    return {
        "query": q,
        "combined_text": combined_text,
        "sources_used": {
            "tavily": bool((tavily_raw.get("results") or [])),
            "serpapi": bool((serp_raw.get("organic_results") or [])),
            "duckduckgo": bool(ddg_raw),
            "news_api": bool(news),
        },
    }


def fetch_case_summary(case_reference: str) -> dict[str, Any]:
    """Deepen context for a named case, docket line, or URL fragment."""
    ref = (case_reference or "").strip()
    if not ref:
        return {"error": "empty case_reference", "summary_text": ""}

    t1 = _tavily_search(f"{ref} legal case court judgment summary")
    lines = _format_tavily(t1)
    if not lines.strip():
        ddg = _duckduckgo_search(ref)
        lines = _format_ddg(ddg)

    return {
        "case_reference": ref,
        "summary_text": lines or "No additional summary could be retrieved.",
    }


def search_case_json(query: str | None = None) -> str:
    """JSON string for MCP tool responses."""
    payload = search_case(query)
    return json.dumps(payload, ensure_ascii=False)


def fetch_case_summary_json(case_reference: str) -> str:
    return json.dumps(fetch_case_summary(case_reference), ensure_ascii=False)
