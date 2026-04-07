from agents import Agent
from schemas import FollowUpPlan

INSTRUCTIONS = """You are a research lead reviewing first-pass web findings.

Given the original research brief (including user clarifications) and concise summaries of searches
already done, decide whether zero to three additional targeted web searches would materially improve
coverage, accuracy, or balance.

If current material is sufficient, set need_follow_up to false and leave searches empty.
Otherwise set need_follow_up to true and add at most three distinct WebSearchItem entries with
clear reasons. Never propose more than three searches."""

expansion_agent = Agent(
    name="ExpansionAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FollowUpPlan,
)
