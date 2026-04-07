from agents import Agent, ModelSettings, WebSearchTool

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, search the web and produce a concise summary "
    "of the results (2–3 short paragraphs, under 300 words). Capture main facts and sources themes; "
    "omit fluff. Output only the summary text."
)

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
