import json
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

mcp = FastMCP("news_server")

_BASE_URL = "https://newsapi.org/v2/top-headlines"


async def _fetch_headlines(params: dict) -> list[dict]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(_BASE_URL, params=params)
        r.raise_for_status()
    articles = r.json().get("articles") or []
    sorted_articles = sorted(articles, key=lambda a: a.get("publishedAt") or "", reverse=True)
    return sorted_articles[:2]


def _format(articles: list[dict]) -> str:
    return json.dumps(
        [
            {
                "title": a.get("title", "(no title)"),
                "source": (a.get("source") or {}).get("name", "unknown"),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", ""),
            }
            for a in articles
        ],
        ensure_ascii=False,
    )


@mcp.tool()
async def headlines_for_country(country_code: str) -> str:
    """Fetch the two most recent top headlines for a country."""
    key = os.getenv("NEWS_API_KEY")
    if not key:
        return "NEWS_API_KEY is not configured."
    try:
        articles = await _fetch_headlines({"country": country_code.lower(), "pageSize": 10, "apiKey": key})
    except Exception as e:
        return f"Failed to fetch headlines: {e}"
    if not articles:
        return f"No headlines found for country '{country_code}'."
    return _format(articles)


@mcp.tool()
async def headlines_for_city(city: str, country_code: str) -> str:
    """Fetch the two most recent headlines for a city within a country."""

    key = os.getenv("NEWS_API_KEY")
    if not key:
        return "NEWS_API_KEY is not configured."
    try:
        articles = await _fetch_headlines({"q": city, "country": country_code.lower(), "pageSize": 10, "apiKey": key})
        if articles:
            return _format(articles)
        fallback = await _fetch_headlines({"country": country_code.lower(), "pageSize": 10, "apiKey": key})
    except Exception as e:
        return f"Failed to fetch headlines: {e}"
    if not fallback:
        return f"No headlines found for '{city}' or country '{country_code}'."
    return json.dumps({"fallback": True, "reason": f"No results for '{city}'", "articles": json.loads(_format(fallback))})


if __name__ == "__main__":
    mcp.run(transport="stdio")
