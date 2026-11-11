from agents import Agent
import os
from dotenv import load_dotenv
from ai_model import anthropic_model
from response_model import WebSearchPlan

load_dotenv(override=True)

HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 5))


INSTRUCTIONS = f"""
You are a research assistant. Given a user query, come up with a set of web searches
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.
"""
planner_agent = Agent(
    name="Planner Agent",
    instructions=INSTRUCTIONS,
    model=anthropic_model,
    output_type=WebSearchPlan,
)
