import os
from tavily import AsyncTavilyClient
from agents import Agent, function_tool, ModelSettings
# from agents import WebSearchTool  # OpenAI hosted search tool 
from model_config import gpt_4o_mini_model
from custom_tracing import custom_trace

tavily_client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@function_tool
async def web_search(query: str) -> str:
    """Search the web for the given query and return a summary of results."""
    async with custom_trace("web_search", kind="TOOL", query=query):
        client = tavily_client
        response = await client.search(
            query,
            max_results=5,
            search_depth="basic",
            # search_depth="advanced",
            include_answer=True,
        )

        sections = []

        if response.get("answer"):
            sections.append(f"## Summary\n{response['answer']}")

        if response.get("results"):
            sections.append("## Sources")
            for r in response["results"]:
                sections.append(f"**{r['title']}**\nSource: {r['url']}\n{r['content']}")

        return "\n\n".join(sections)


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
    tools=[web_search],
    # tools=[WebSearchTool(search_context_size="low")],  # OpenAI WebSearchTool alternative
    model=gpt_4o_mini_model,
    # model="gpt-4o-mini",  # required when using WebSearchTool above
    model_settings=ModelSettings(tool_choice="required"),
)
