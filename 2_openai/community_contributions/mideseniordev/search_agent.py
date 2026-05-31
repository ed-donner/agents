from agents import Agent, ModelSettings, WebSearchTool

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You execute one web search task at a time and summarize findings for downstream synthesis.

Output rules:
- 2-3 short paragraphs
- under 220 words
- include concrete findings, avoid fluff
- include source URLs when available
- no extra commentary
"""


search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model=DEFAULT_MODEL,
    model_settings=ModelSettings(tool_choice="required"),
)
