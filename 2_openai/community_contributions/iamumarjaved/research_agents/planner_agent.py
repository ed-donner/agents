from pydantic import BaseModel, Field
from agents import Agent

# Number of searches to perform
HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a highly skilled research assistant specializing in creating comprehensive search strategies.

You will receive:
1. The original research query
2. Three clarifying questions that were asked
3. The user's answers to those questions

Your task is to:
1. Analyze the query in light of the clarifications provided
2. Use the user's answers to tune and refine your search strategy
3. Create {HOW_MANY_SEARCHES} highly targeted, strategic search queries
4. Ensure searches align with the user's specific interests and goals as revealed by their answers

The clarifications help you understand:
- What aspects the user cares about most
- The desired depth and scope
- Specific angles or perspectives to prioritize
- What to emphasize or de-emphasize

Create search terms that:
- Directly address the user's clarified interests
- Cover different complementary aspects
- Use the clarifications to be more specific and relevant
- Avoid areas the user indicated they're not interested in
- Balance breadth with the focused depth the user wants

Output {HOW_MANY_SEARCHES} strategic web search terms that are precisely tuned to what the user actually wants to know.
"""


class WebSearchItem(BaseModel):
    """Individual web search with reasoning"""
    reason: str = Field(
        description="Detailed reasoning explaining how this search addresses the original query AND the user's clarifications"
    )
    query: str = Field(
        description="The optimized search term, tuned based on the clarifications. Should be specific and targeted."
    )


class WebSearchPlan(BaseModel):
    """Complete search strategy tuned to user's clarified needs"""
    searches: list[WebSearchItem] = Field(
        description=f"A list of {HOW_MANY_SEARCHES} strategically planned searches, carefully tuned based on the user's clarifications"
    )
    
    strategy_summary: str = Field(
        description="Brief explanation of how the search strategy was adapted based on the user's clarifications"
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

