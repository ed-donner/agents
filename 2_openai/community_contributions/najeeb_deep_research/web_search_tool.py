import os
from dotenv import load_dotenv
from agents import function_tool
import httpx

load_dotenv(override=True)
serper_api_key = os.getenv("SERPER_API_KEY")

@function_tool
def serper_web_search(query: str) -> str:
    """Search the web via Serper (Google results). Returns titles, snippets, and URLs."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://google.serper.dev/search",
                json={"q": query},
                headers={"X-API-KEY": serper_api_key, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return f"Serper API request failed: {e}"

    organic = data.get("organic") or []
    if not organic:
        return "No search results returned (empty organic results)."

    parts = []
    for i, item in enumerate(organic[:10], 1):
        title = item.get("title") or "(no title)"
        link = item.get("link") or ""
        snippet = item.get("snippet") or ""
        parts.append(f"{i}. **{title}**\n   {snippet}\n   URL: {link}")
    return "\n\n".join(parts)