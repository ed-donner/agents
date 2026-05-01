from agents import Agent, Runner
from pydantic import BaseModel


class ClarificationQuestions(BaseModel):
    questions: list[str]
    is_clear_enough: bool

CLARIFICATION_PROMPT = """
You are a research intake specialist. Your job is to identify ambiguities 
in a research query and ask targeted follow-up questions BEFORE research begins.
Ask 2-3 short, specific questions only if genuinely needed.
If the query is already specific enough, set is_clear_enough=True.
Focus on: scope, depth, perspective, time-range, use-case.
Do NOT ask vague or redundant questions.
"""

clarification_agent = Agent(
    name="Clarification Agent",
    instructions=CLARIFICATION_PROMPT,
    output_type=ClarificationQuestions,
    model="gpt-4o-mini",
)


clarification_tool = clarification_agent.as_tool(
    tool_name="clarify_query",
    tool_description="Use this to ask clarifying questions when a research query is vague or ambiguous. Returns questions to ask the user.",
)
