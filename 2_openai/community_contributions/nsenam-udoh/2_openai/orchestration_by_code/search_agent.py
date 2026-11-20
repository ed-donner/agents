from agents import Agent, ModelSettings, WebSearchTool

from planner_agent import MODEL_NAME

INSTRUCTIONS = """
You are a research assistant. Given a search term and any clarification answers,
search the web and produce a concise summary of the results. The summary must be
2-3 paragraphs and less than 300 words. Capture the main points and be succinct.
Reply only with the summary.
"""

settings = ModelSettings(tool_choice="required")
tools = [WebSearchTool()]

search_agent = Agent(
    name="Search Agent",
    instructions=INSTRUCTIONS,
    tools=tools,
    model=MODEL_NAME,
    model_settings=settings,
)
