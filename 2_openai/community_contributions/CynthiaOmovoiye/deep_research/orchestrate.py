"""ResearchHost, ResearchLead, clarifier, and tools."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic import BaseModel, Field

import compat  # noqa: F401
from agents import Agent, GuardrailFunctionOutput, Runner, function_tool, handoff, input_guardrail
from agents.run_context import RunContextWrapper
from pipeline import ResearchManager


@dataclass
class ResearchUiContext:
    """Set by the Gradio layer each turn so tools use the real transcript, not only LLM tool args."""

    topic: str = ""
    prior_qa_block: str = ""


def _is_assistant_placeholder(assistant_text: str) -> bool:
    s = (assistant_text or "").strip()
    if not s:
        return True
    if s.startswith("_Thinking"):
        return True
    if s.startswith("_Run error"):
        return True
    # Gradio streams ephemeral status as italic: _status_
    if len(s) > 2 and s.startswith("_") and s.endswith("_"):
        return True
    return False


def clarifier_topic_and_prior_from_gradio(history: list) -> tuple[str, str]:
    """Derive research topic and prior clarifying Q&A from Gradio [user, assistant] rows."""
    if not history:
        return "", ""
    row0 = history[0]
    if not isinstance(row0, (list, tuple)) or len(row0) < 1:
        return "", ""
    topic = (row0[0] or "").strip() if isinstance(row0[0], str) else ""
    lines: list[str] = []
    n = len(history)
    for i in range(n):
        row = history[i]
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        u_raw, a_raw = row[0], row[1]
        u = (u_raw or "").strip() if isinstance(u_raw, str) else ""
        a = (a_raw or "").strip() if isinstance(a_raw, str) else ""
        if i == 0:
            if a and not _is_assistant_placeholder(a):
                lines.append(f"Q1: {a}")
            continue
        if u:
            lines.append(f"A{i}: {u}")
        is_last = i == n - 1
        if not is_last and a and not _is_assistant_placeholder(a):
            lines.append(f"Q{i + 1}: {a}")
    return topic, "\n".join(lines)


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
    "Each question must build on previous answers: do not re-ask what the user already "
    "specified (e.g. if they chose theological, do not ask philosophy vs theology again). "
    "Narrow a *new* dimension: audience, tradition, timeframe, depth, geographic scope, "
    "or concrete deliverable. "
    "Do not repeat earlier questions. "
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
    ctx: RunContextWrapper[ResearchUiContext],
    topic: str,
    prior_questions_and_answers: str,
    question_index: int,
) -> str:
    """Generate clarifying question `question_index` (must be 1, 2, or 3).

    `topic` and `prior_questions_and_answers` are hints from the host; the app may inject
    the canonical transcript via run context (preferred when present).
    """
    if question_index not in (1, 2, 3):
        return "Error: question_index must be 1, 2, or 3."
    c = ctx.context
    canon_topic = (c.topic or topic or "").strip()
    canon_prior = (c.prior_qa_block or prior_questions_and_answers or "").strip()
    prior = canon_prior or "(none yet)"
    prompt = (
        f"Research topic (from user):\n{canon_topic}\n\n"
        f"Prior clarifying Q&A so far:\n{prior}\n\n"
        f"Produce clarifying question #{question_index} of 3. "
        "It must not repeat an earlier question and must build on prior answers."
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

research_lead_agent = Agent[ResearchUiContext](
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

research_host_agent = Agent[ResearchUiContext](
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
