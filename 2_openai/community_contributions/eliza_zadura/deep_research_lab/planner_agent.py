"""
Planner Agent - creates the search strategy based on the research brief.

This agent:
- Receives the locked ResearchBrief
- Outputs query clusters with source tier preferences
- Defines stop conditions for search completeness

The planner is source-policy-aware: it knows to prioritize primary sources
and guides the search executor on what quality of sources to seek.
"""

from agents import Agent, AgentOutputSchema
from models import SearchPlan


INSTRUCTIONS = """You are a research planner. Given a research brief, create a comprehensive search strategy.

Your job is to:
1. Generate 5-7 search queries that will thoroughly cover the research topic
2. For each query, explain why it's important and what source types would be ideal
3. Set a stop condition (minimum sources needed)
4. Note any source policy guidance

## Source Quality Policy

Treat the internet as adversarial. Prioritize sources in this order:
1. **PRIMARY**: Official docs, academic papers, SEC filings, government data (most trusted)
2. **SECONDARY**: Reputable news outlets, established industry analysts
3. **VENDOR**: Company marketing material (allowed but must be labeled as such)
4. **OPINION**: Blogs, opinion pieces (use for framing/context only, not facts)
5. **EXCLUDED**: Social media posts (do not use)

## Query Strategy

- Mix broad and specific queries
- Include queries that might surface primary sources (e.g., "site:gov", "filetype:pdf")
- Consider the desired_angle from the brief (best_case vs risks vs balanced)
- If scope constraints exist, incorporate them into queries

Be thorough but focused. Quality over quantity.
"""

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=AgentOutputSchema(SearchPlan, strict_json_schema=False),
)
