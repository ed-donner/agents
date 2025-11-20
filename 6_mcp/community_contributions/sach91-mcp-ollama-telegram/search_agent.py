from agents import Agent
from base_model import ollama_model

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term "
    "using the tool provided by the MCP Server. "
    "Capture the main points from the search results in less than 300 words. "
    "Write succinctly, no need to have complete sentences or good grammar. "
    "This will be consumed by someone synthesizing a report, so its vital you capture the essence. "
)


def get_search_agent(mcp_server) -> Agent:
    search_agent = Agent(
        name="SearchAgent",
        instructions=INSTRUCTIONS,
        model=ollama_model,
        mcp_servers=[mcp_server],
    )
    print('Created Search Agent.')
    return search_agent
