from agents import Agent
from schemas import WebSearchItem, WebSearchPlan

HOW_MANY_SEARCHES = 3

INSTRUCTIONS = f"""You are a research planner. Given a query and optional user clarifications,
propose exactly {HOW_MANY_SEARCHES} web searches that together best answer the brief.
Prefer diverse angles (definition, recent developments, risks, applications, comparisons) rather than
near-duplicate queries."""

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
