from agents import Agent

from llm import balanced_model_settings, small_model
from schemas import WebSearchPlan

INSTRUCTIONS = """You design the next search round for a deep research workflow.

The input may include:
- the original query
- clarifying Q&A
- the enriched query
- the current round number
- prior findings
- identified coverage gaps

Rules:
- Return only the next round's plan, not a final answer.
- Use broad foundational searches in round 1.
- In later rounds, focus tightly on unresolved gaps and avoid redundant searches.
- Prefer source-oriented queries that are likely to produce concrete evidence.
- Keep the search set small and high-value."""

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=small_model,
    model_settings=balanced_model_settings,
    output_type=WebSearchPlan,
)
