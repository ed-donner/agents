from datetime import date
from agents import Agent, WebSearchTool, ModelSettings

TODAY = date.today().isoformat()

INSTRUCTIONS = (
    f"You are a research assistant. Today is {TODAY}. "
    "Given a search term, search the web and produce a concise summary of the results. "
    "2-3 paragraphs, under 300 words. Prioritize recent sources. "
    "Write succintly — no fluff, no commentary."
)

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required", temperature=0.0, max_tokens=500),
)
