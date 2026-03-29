from agents import Agent, function_tool, ModelSettings, Runner
from poor_man_web_search import local_web_search

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)


@function_tool
def MockWebSearchTool(query: str) -> str:
    """Search the web for the given query and return a concise summary of the results."""
    results = local_web_search(query)
    summary = "\n\n".join(
        [f"URL: {item['page_url']}\nContent: {item['content']}" for item in results]
    )
    return summary


search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[MockWebSearchTool],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
