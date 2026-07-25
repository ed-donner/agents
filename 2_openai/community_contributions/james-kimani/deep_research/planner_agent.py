from datetime import date
from agents import Agent, ModelSettings
from schemas import WebSearchPlan

HOW_MANY_SEARCHES = 1
CURRENT_YEAR = date.today().year

INSTRUCTIONS = (
    f"You are a helpful research assistant. Given a query, come up with a set of web searches "
    f"to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for. "
    f"For time-sensitive topics, include the year ({CURRENT_YEAR}) in the search term."
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
    model_settings=ModelSettings(temperature=0.0, max_tokens=400),
)
