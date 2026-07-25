import os
import requests
from agents import Agent, ModelSettings, function_tool

from config import model


@function_tool
def serper_search(query: str) -> str:
    """Perform web search via Serper API. Use this for the given search term."""
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return "SERPER_API_KEY not set; cannot run web search."
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 10}
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        out = f"Search results for: {query}\n\n"
        if "organic" in data:
            for i, item in enumerate(data["organic"][:5], 1):
                out += f"{i}. **{item.get('title', '')}**\n"
                out += f"   {item.get('snippet', '')}\n"
                out += f"   Source: {item.get('link', '')}\n\n"
        if "knowledgeGraph" in data and data["knowledgeGraph"].get("description"):
            out += f"\n**Key info:** {data['knowledgeGraph']['description']}\n"
        return out.strip() or "No results found."
    except Exception as e:
        return f"Search failed: {e!s}"


INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[serper_search],
    model=model,
    model_settings=ModelSettings(tool_choice="required"),
)

search_agent_tool = search_agent.as_tool(
    tool_name="search_tool",
    tool_description="Performs a web search for a given term and returns a short summary.",
)
