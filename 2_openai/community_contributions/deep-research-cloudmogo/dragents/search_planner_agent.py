from agents import Agent, Runner

from models.models import WebSearchPlan

HOW_MANY_SEARCHES = 3
PLANNING_INSTRUCTIONS = f"You are a helpful research assistence. Given a query, come up with a set of the web searches \
    to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

planner_agent = Agent(
    name = "Search Planner Agent",
    instructions= PLANNING_INSTRUCTIONS,
    model = "gpt-4o-mini",
    output_type=WebSearchPlan,
 )