from agents import Agent, ModelSettings, WebSearchTool


PERFORM_SEARCH_INSTRUCTIONS = " You are a research assistant. Given a search term, you search the web for that term and \
produce a concise summary of the resluts. The summary must 2-3 paragraphs and less than 300 \
words. Capture the emain points. Write succiently, no need to have complete sentances or good grammer. \
This will be consumed by someone synthesizing a report, so it's vital your capture the \
essence and ignore any fluff. DO not include any additional commenary other than the summary itself."

search_agent = Agent(
    name = "Search Agent",
    instructions=PERFORM_SEARCH_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="low")],
    model_settings=ModelSettings(tool_choice="required"),
)