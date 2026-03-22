from agents import Agent, WebSearchTool, ModelSettings, function_tool
import os
import httpx
from bs4 import BeautifulSoup

from openai_compat import AGENT_MODEL

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

_use_openrouter_web_fallback = bool(os.getenv("OPENROUTER_API_KEY"))

@function_tool
async def web_search(query: str) -> str:
    """Search the web and return titles and snippets from top DuckDuckGo results."""
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AgentsCourse/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ) as client:
        response = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
        )
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    lines: list[str] = []
    for res in soup.select("div.result")[:10]:
        a = res.select_one("a.result__a")
        if not a:
            continue
        title = a.get_text(strip=True)
        snip = res.select_one(".result__snippet")
        snippet = snip.get_text(strip=True) if snip else ""
        lines.append(f"- {title}: {snippet}".strip())
    if not lines:
        return f"(No results parsed for {query!r}. Try a shorter query or check your network.)"
    return "\n".join(lines)


_search_tools = (
    [web_search]
    if _use_openrouter_web_fallback
    else [WebSearchTool(search_context_size="low")]
)
search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=_search_tools,
    model=AGENT_MODEL,
    model_settings=ModelSettings(tool_choice="required"),
)