"""
research_agent.py — Runs individual web searches and returns concise summaries.
Uses DuckDuckGo (DDGS) as a free, no-API-key search engine.
"""
from agents import Agent, function_tool
from agents.model_settings import ModelSettings
from ddgs import DDGS
from deep_research import LITELLM_FAST


# ── Tool ─────────────────────────────────────────────────────────────────────

@function_tool
def search_the_web(query: str) -> str:
    """Searches the web for the given query and returns the top results."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            results.append(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n"
            )
    return "\n---\n".join(results) if results else "No results found."


# ── Agent definition ─────────────────────────────────────────────────────────

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web and "
    "produce a concise summary of the results in 2-3 paragraphs (under 300 words). "
    "Capture the main points. Write succinctly — no need for complete sentences or "
    "perfect grammar. **Always include the source URLs (links) for the information you "
    "find in your summary.** Do not add commentary beyond the summary itself."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[search_the_web],
    model=LITELLM_FAST,
    model_settings=ModelSettings(tool_choice="required"),
)
