from pydantic import BaseModel, Field
from agents import Agent

CLARIFYING_LIMIT = 5

INSTRUCTIONS = f"""You are a research assistant helping to clarify the user's research topic before starting.

Given the conversation so far and the latest user message:
1. If the research topic is still vague or under-specified, respond with clarifying questions (up to {CLARIFYING_LIMIT}).
   Set ready_to_research=False and put your response in message. Leave refined_query empty.
2. If the user has provided enough information (either initially or after your questions), set ready_to_research=True,
   put a clear, specific refined_query that captures what to research, and a brief message confirming we can start (e.g. "I have enough to start. Here's what I'll research: ...").
3. If the user says they want to "start research" or "go ahead" or similar, treat that as confirmation and output ready_to_research=True with the best refined_query you can infer from the conversation.

Always output valid JSON with message, ready_to_research, and refined_query (use empty string when not ready).
"""


class ClarifierOutput(BaseModel):
    message: str = Field(description="Your reply to the user: either clarifying questions or confirmation that we can start.")
    ready_to_research: bool = Field(description="True only when we have a clear research query and can start the full research pipeline.")
    refined_query: str = Field(default="", description="When ready_to_research is True, the specific research query to run. Otherwise empty string.")


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifierOutput,
)
