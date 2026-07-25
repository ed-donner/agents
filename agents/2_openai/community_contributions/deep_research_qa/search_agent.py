from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so it's vital you capture the "
    "essence and ignore any fluff. "
    
    "IMPORTANT: Always preserve and include the source URLs that are provided in the search results. "
    "When you mention information from a source, include the URL reference in the format: (source.com) "
    "or [Title](URL). Keep all source links intact in your summary."
    
    "Do not include any additional commentary other than the summary itself with preserved source links."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)