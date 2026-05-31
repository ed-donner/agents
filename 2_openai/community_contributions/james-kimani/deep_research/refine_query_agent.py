from agents import Agent, ModelSettings
from schemas import RefinedQuery

INSTRUCTIONS = (
    "You refine user research requests into one clear, specific question or topic statement. "
    "Resolve ambiguity, suggest sensible scope if the user was vague, and keep the output "
    "usable for web search and synthesis. Do not perform research yourself; only rewrite."
)

refine_query_agent = Agent(
    name="RefineQueryAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RefinedQuery,
    model_settings=ModelSettings(temperature=0.0, max_tokens=350),
)
