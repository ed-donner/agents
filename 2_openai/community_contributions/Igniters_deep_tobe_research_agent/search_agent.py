from agents import Agent, ModelSettings

from llm import small_model
from schemas import SearchEvidence
from search_tools import search_web

INSTRUCTIONS = """You handle one research search at a time.

You will receive a search query and the reason it matters.
You must call `search_web` exactly once, then synthesize the returned evidence.

Rules:
- Ground your output in the search results and extracted page text only.
- Focus on the facts most useful for later report writing.
- Keep the summary concise but information-dense.
- Include only source URLs that appear in the tool output."""

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    model=small_model,
    model_settings=ModelSettings(temperature=0.1, tool_choice="required"),
    tools=[search_web],
    output_type=SearchEvidence,
)
