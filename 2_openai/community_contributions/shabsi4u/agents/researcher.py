from agents import Agent, ModelSettings, WebSearchTool

from core.state import ResearchResult


INSTRUCTIONS = """
You are a research agent inside a deep research system.

Use web search to investigate the user's clarified request. Convert the request and clarification
answers into focused search activity, then synthesize what you found.

Requirements:
- Use web search before responding.
- Keep the research focused on the clarified scope.
- Return a small number of search queries actually used.
- Distill the most important findings.
- Cite supporting evidence with source names and URLs.
- Identify obvious remaining gaps honestly.
"""


researcher_agent = Agent(
    name="ResearcherAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="medium")],
    model_settings=ModelSettings(tool_choice="required"),
    output_type=ResearchResult,
)
