from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself.\n\n"
    "**Citation requirement**: At the end of your summary, add exactly one line in this format:\n"
    "Source: <URL or title of the most relevant result from your search>\n"
    "This allows the report to cite your summary. If no URL/title is available, use: Source: [Web search for: <search term>]"
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

search_agent_tool = search_agent.as_tool(
    tool_name="web_search",
    tool_description="Run one web search for a given term and return a concise summary (2–3 paragraphs). Call once per search term.",
)