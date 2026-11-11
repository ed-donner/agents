from crewai.tools import tool
from ddgs import DDGS


@tool("Web Search")
def web_search(query: str) -> str:
    """
    Use this tool to search the web and the latest news. Free DuckDuckGo search, no API key needed.
    Args:
        query: The search query.
    Returns:
        The title, link and snippet of the top news and web results.
    """
    results = []
    with DDGS() as ddgs:
        # news can come back empty for niche queries, so a failure there shouldn't lose the web results
        for search in (ddgs.news, ddgs.text):
            try:
                results += search(query, max_results=5)
            except Exception as e:
                results.append({"title": f"{search.__name__} search failed", "body": str(e)})
    return "\n\n".join(
        f"{r.get('title')}\n{r.get('url') or r.get('href') or ''}\n{r.get('date', '')} {r.get('body')}".strip()
        for r in results
    ) or "No results found."
