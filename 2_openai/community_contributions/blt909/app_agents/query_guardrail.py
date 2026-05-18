from pydantic import BaseModel, Field
from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput, RunContextWrapper
from typing import Any


class ClarificationQuestions(BaseModel):
    needs_clarification: bool = Field(
        description="Whether the query needs clarification before proceeding."
    )
    questions: list[str] = Field(
        description="A list of 1 to 3 concise clarifying questions to ask the user. "
                    "Empty if needs_clarification is False."
    )


INSTRUCTIONS = (
    "You are a query evaluator for a newsletter generation service. "
    "Given a user query, assess whether it is specific enough to generate a high-quality newsletter.\n\n"
    "If the query is clear and sufficiently specific, set needs_clarification to False and return an empty list.\n\n"
    "If the query is vague, too broad, or ambiguous, set needs_clarification to True and return "
    "1 to 3 concise, targeted questions that, when answered, would give enough context to produce "
    "the best possible newsletter. Focus on:\n"
    "- Target audience (e.g., experts vs. general public)\n"
    "- Scope or time frame (e.g., recent developments, historical overview)\n"
    "- Angle or perspective (e.g., technical, business impact, geopolitics)\n\n"
    "Never accept a query that is not specific enough to generate a high-quality newsletter.\n"
    "Never accept a query under 10 words and without a clear topic.\n"
    "Do not ask more than 3 questions. Prefer fewer, higher-impact questions."
)

_query_guardrail_agent = Agent(
    name="Query Guardrail",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)


@input_guardrail(name="query_clarity_guardrail")
async def query_clarity_guardrail(
    context: RunContextWrapper[Any],
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """Guardrail that trips if the user query needs clarification before research can begin."""
    result = await Runner.run(_query_guardrail_agent, input, context=context.context)
    clarification = result.final_output_as(ClarificationQuestions)

    return GuardrailFunctionOutput(
        output_info=clarification,
        tripwire_triggered=clarification.needs_clarification,
    )
