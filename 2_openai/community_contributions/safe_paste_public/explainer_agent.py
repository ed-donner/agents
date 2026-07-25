"""Agent 3: explain errors/logs — only wired when scanner says low/medium risk."""

from agents import Agent

from leak_guardrail import leak_input_guardrail
from models import ExplainerResult

INSTRUCTIONS = """
You explain technical errors, stack traces, and HTTP/API responses to a developer.

Rules:
- Do not reproduce or guess secret values; if the paste might still contain secrets, say so briefly.
- Prefer structured diagnosis: what failed, where, and what to try next.
- If information is missing for a confident fix, list what to collect next (without asking for secrets).

Output must follow the schema: summary, likely_causes, next_steps, cautions.
"""

explainer_agent = Agent(
    name="ErrorExplainerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ExplainerResult,
    input_guardrails=[leak_input_guardrail],
)
