from typing import List, Dict
from ddgs import DDGS

def web_search(query: str, safe_search: str = "moderate") -> List[Dict[str, str]]:
    """
    Search the web with DuckDuckGo and return up the results.
    safe_search: "off" | "moderate" | "strict"
    """
    max_results = 1
    results: List[Dict[str, str]] = []
    # ddg regions: "wt-wt" is worldwide; you can add region=... if you want localization
    with DDGS() as ddgs:
        for r in ddgs.text(query, safesearch=safe_search, max_results=max_results, backend="lite"):
            results.append({
                "title": r.get("title") or "",
                "url": r.get("href") or r.get("url") or "",
                "snippet": r.get("body") or r.get("snippet") or ""
            })
    return results

