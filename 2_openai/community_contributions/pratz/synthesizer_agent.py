from agents import Agent
from pydantic import BaseModel

class RefinedQuery(BaseModel):
    refined_query: str

SYNTHESIS_PROMPT = """
You are a research query synthesizer. Given an original query and the user's 
answers to clarification questions, produce a single, enriched research query 
that captures all the nuance and context. Return a concise but detailed query 
string that goes directly to a deep research engine.
"""

synthesis_agent = Agent(
    name="Synthesis Agent",
    instructions=SYNTHESIS_PROMPT,
    output_type=RefinedQuery,
    model="gpt-4o-mini",
)

synthesis_tool = synthesis_agent.as_tool(
    tool_name="synthesize_query",
    tool_description="Use this after the user has answered clarifying questions. Pass the original query and Q&A pairs to get a refined research query.",
)

