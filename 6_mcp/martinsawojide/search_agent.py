from agents import Agent, ModelSettings

from model_config import gpt_4o_mini_model

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you use your Tavily web search tool "
    "for that term and produce a concise summary of the results. The summary must be 2-3 paragraphs "
    "and less than 300 words. Capture the main points. Write succinctly; complete sentences and "
    "perfect grammar are not required. This will be consumed by someone synthesizing a report, so "
    "capture the essence and ignore fluff. Do not include any additional commentary other than "
    "the summary itself."
)


def build_search_agent(mcp_servers: list) -> Agent:
    return Agent(
        name="Search agent",
        instructions=SEARCH_INSTRUCTIONS,
        tools=[],
        mcp_servers=mcp_servers,
        model=gpt_4o_mini_model,
        model_settings=ModelSettings(tool_choice="required"),
    )
