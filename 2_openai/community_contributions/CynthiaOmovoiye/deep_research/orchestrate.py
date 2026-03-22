"""ResearchHost, ResearchLead, clarifier, and tools."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

import compat  # noqa: F401
from agents import Agent, GuardrailFunctionOutput, Runner, function_tool, handoff, input_guardrail
from pipeline import ResearchManager

# Gradio registers this before each streamed run. ContextVar is unreliable here because
# tool execution may run without the chat task's context, so the queue is module-global.
_progress_queue: asyncio.Queue[str] | None = None


def set_research_progress_queue(q: asyncio.Queue[str] | None) -> None:
    global _progress_queue
    _progress_queue = q


async def _push_progress(line: str) -> None:
    q = _progress_queue
    if q is not None:
        await q.put(line)


class ClarifyingQuestionOutput(BaseModel):
    question: str = Field(description="One concise clarifying question (one sentence if possible).")


CLARIFIER_INSTRUCTIONS = (
    "You help narrow a research request. Given the user's topic and any prior Q&A, "
    "you write exactly ONE new clarifying question. "
    "Questions should narrow scope, audience, timeframe, depth, or constraints. "
    "Do not repeat a question that was already asked. "
    "Output only via the structured field."
)

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=CLARIFIER_INSTRUCTIONS,
    model=compat.AGENT_MODEL,
    output_type=ClarifyingQuestionOutput,
)


@function_tool
async def next_clarifying_question(
    topic: str,
    prior_questions_and_answers: str,
    question_index: int,
) -> str:
    """Generate clarifying question `question_index` (must be 1, 2, or 3).

    `topic` is the user's research topic from their first message.
    `prior_questions_and_answers` lists earlier Q&A (plain text). Use empty string if none.
    """
    if question_index not in (1, 2, 3):
        return "Error: question_index must be 1, 2, or 3."
    prior = (prior_questions_and_answers or "").strip() or "(none yet)"
    prompt = (
        f"Research topic (from user):\n{topic}\n\n"
        f"Prior clarifying Q&A so far:\n{prior}\n\n"
        f"Produce clarifying question #{question_index} of 3. "
        "It must not repeat an earlier question."
    )
    result = await Runner.run(clarifier_agent, prompt)
    q = result.final_output_as(ClarifyingQuestionOutput)
    return q.question


@function_tool
async def run_deep_research(research_brief: str) -> str:
    """Run the full web research pipeline (plan → search → write → email).

    `research_brief` must include the user's topic and all three clarifying Q&A pairs in plain text.
    Returns status lines and the final markdown report.
    """
    parts: list[str] = []
    try:
        async for chunk in ResearchManager().run(research_brief, on_progress=_push_progress):
            parts.append(str(chunk))
    except Exception as exc:
        parts.append(f"Research pipeline error: {exc}")
    if not parts:
        return "No output from research pipeline."
    return "\n\n---\n\n".join(parts)


RESEARCH_LEAD_INSTRUCTIONS = (
    "You are the Research Lead. The user has already answered three clarifying questions in the "
    "conversation. Your only job:\n"
    "1. Read the full conversation and build one `research_brief` string that includes the "
    "original topic and all three Q&A pairs, clearly labeled.\n"
    "2. Call the tool `run_deep_research` exactly once with that brief.\n"
    "3. Reply to the user with the tool result (the report and status text). "
    "Do not call the tool again unless the tool failed with a clear error."
)

research_lead_agent = Agent(
    name="ResearchLead",
    instructions=RESEARCH_LEAD_INSTRUCTIONS,
    tools=[run_deep_research],
    model=compat.AGENT_MODEL,
    handoff_description=(
        "Hand off here after the user has answered all three clarifying questions "
        "to run full web research and produce the report."
    ),
)


@input_guardrail
async def nonempty_user_message(ctx, agent, message) -> GuardrailFunctionOutput:
    if isinstance(message, str):
        text = message.strip()
    else:
        text = str(message).strip()
    return GuardrailFunctionOutput(
        output_info={"length": len(text)},
        tripwire_triggered=len(text) == 0,
    )


HOST_INSTRUCTIONS = """
You are ResearchHost. You manage a single research session over chat (session memory is kept for you).

## Phase A — Three clarifying questions
1. The user's FIRST message is the research **topic**. Remember it exactly for tool calls.
2. For question 1: call `next_clarifying_question` with:
   - `topic` = that first message (verbatim topic)
   - `prior_questions_and_answers` = empty string
   - `question_index` = 1
   Then show the user **only** that question in friendly text (no extra lecturing).
3. When the user answers, call the tool again with `question_index` = 2 and
   `prior_questions_and_answers` listing Q1 and their answer, then show question 2.
4. Repeat for `question_index` = 3 with prior Q&A including 1 and 2.

## Phase B — Hand off to research
5. After the user answers the **third** question, do **not** ask more clarifying questions.
6. Call the handoff tool `transfer_to_research_lead` (no arguments). The Research Lead will run
   web research using the full conversation context.

## Rules
- Never skip a question index; never ask more than three clarifying questions before handoff.
- If the user drifts off-topic, gently steer back.
- Keep messages concise.
"""

research_host_agent = Agent(
    name="ResearchHost",
    instructions=HOST_INSTRUCTIONS,
    tools=[next_clarifying_question],
    handoffs=[
        handoff(
            research_lead_agent,
            tool_name_override="transfer_to_research_lead",
        )
    ],
    model=compat.AGENT_MODEL,
    input_guardrails=[nonempty_user_message],
)
