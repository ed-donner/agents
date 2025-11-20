from agents import Agent, ModelSettings, function_tool
from base_model import ollama_model
from typing import List, Dict
from ddgs import DDGS

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

@function_tool
def web_search(query: str, safe_search: str = "moderate") -> List[Dict[str, str]]:
    """
    Search the web with DuckDuckGo and return up the results.
    safe_search: "off" | "moderate" | "strict"
    """
    max_results = 1
    print('Web search Query ->', query)
    results: List[Dict[str, str]] = []
    # ddg regions: "wt-wt" is worldwide; you can add region=... if you want localization
    with DDGS() as ddgs:
        for r in ddgs.text(query, safesearch=safe_search, max_results=max_results):
            results.append({
                "title": r.get("title") or "",
                "url": r.get("href") or r.get("url") or "",
                "snippet": r.get("body") or r.get("snippet") or ""
            })
    print('Web search result ->', results)
    return results

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[web_search],
    model=ollama_model,
    model_settings=ModelSettings(tool_choice="required"),
)