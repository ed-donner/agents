"""Week 2 agents (OpenAI Agents SDK).

- **Clarifying** — structured clarifying questions for ambiguous user input.
- **Deep research** — one agent with ``WebSearchTool`` that returns a concise answer summary.
- **Evaluator** — judges whether the research summary fits the original request and clarifying choice.
- **Orchestrator** — talks to the user: detects research requests, runs clarify → research → evaluate,
  and composes the final reply via ``orchestrator_agent``.

Configure ``OPENAI_API_KEY`` before calling. Web search is billable per OpenAI pricing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agents import Agent, Runner, WebSearchTool, trace
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-4o-mini"
MAX_CLARIFYING_QUESTIONS = 3

# --- Clarifying agent ---

CLARIFY_INSTRUCTIONS = f"""You read the user's message and decide what you still need to know to help well.

Produce up to {MAX_CLARIFYING_QUESTIONS} clarifying questions, ordered from most to least important.
Each question should be concrete and easy for the user to answer in one or two sentences.

Focus on gaps such as: goal, constraints, audience, format, time horizon, success criteria,
domain-specific details, or anything they implied but did not state.

If the message is already clear enough, return few or no questions and say so briefly in your summary."""


class ClarifyingQuestion(BaseModel):
    question: str = Field(description="A single clarifying question for the user.")
    why_it_matters: str = Field(
        description="One short sentence on what ambiguity this question resolves."
    )


class ClarifyingQuestionsResult(BaseModel):
    understood_so_far: str = Field(
        description="Brief paraphrase of what you understood from the user's input."
    )
    questions: list[ClarifyingQuestion] = Field(
        default_factory=list,
        description=f"Up to {MAX_CLARIFYING_QUESTIONS} prioritized clarifying questions.",
    )


clarifying_agent = Agent(
    name="ClarifyingQuestionsAgent",
    instructions=CLARIFY_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ClarifyingQuestionsResult,
)


async def clarify(user_input: str) -> ClarifyingQuestionsResult:
    """Run the clarifying agent on the user's text and return structured questions."""
    text = (user_input or "").strip()
    if not text:
        return ClarifyingQuestionsResult(
            understood_so_far="No input was provided.",
            questions=[],
        )
    result = await Runner.run(clarifying_agent, text)
    return result.final_output


# --- Deep research agent ---

RESEARCH_INSTRUCTIONS = """You are a research assistant with access to web search.

Use search when you need current or factual information to answer the user's message. Search as many times as needed to be confident, then stop.

Your final reply must be a clear, accurate summary that directly answers what they asked—no preamble, no meta commentary about searching."""

deep_research_agent = Agent(
    name="DeepResearchAgent",
    instructions=RESEARCH_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    tools=[WebSearchTool(search_context_size="low")],
)


async def deep_research(user_input: str) -> str:
    """Run the deep-research agent and return the best answer summary."""
    text = (user_input or "").strip()
    if not text:
        return ""
    result = await Runner.run(deep_research_agent, text)
    return str(result.final_output)


# --- Evaluator agent ---

EVALUATOR_INSTRUCTIONS = """You evaluate a deep-research summary (you do not use web search).

You are given, in order:
1) The user's original request
2) The user's clarifying choice — what they answered, selected, or decided after clarifying questions (constraints, priorities, format, etc.)
3) The deep-research summary to judge

Decide whether (3) correctly and adequately addresses what the user wanted, taking (1) and (2) together.

Mark the outcome correct only if the summary is on-topic, respects constraints from the clarifying choice, and is internally coherent. If the summary ignores an important part of (2), or answers the wrong question, mark it incorrect.

You cannot verify raw facts against the live web; flag only clear logical gaps, irrelevance, or contradictions with (1)/(2)."""


class ResearchEvaluation(BaseModel):
    is_correct: bool = Field(
        description="True if the research summary adequately addresses the request given the original input and clarifying choice."
    )
    rationale: str = Field(description="Short justification referencing the original request and clarifications.")
    issues: list[str] = Field(
        default_factory=list,
        description="Concrete gaps, errors, or missing aspects; empty if none.",
    )


evaluator_agent = Agent(
    name="ResearchEvaluatorAgent",
    instructions=EVALUATOR_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ResearchEvaluation,
)


async def evaluate_research(
    initial_user_input: str,
    clarifying_choice: str,
    research_result: str,
) -> ResearchEvaluation:
    """Judge whether ``research_result`` fits ``initial_user_input`` and ``clarifying_choice``."""
    research = (research_result or "").strip()
    if not research:
        return ResearchEvaluation(
            is_correct=False,
            rationale="No research output was provided to evaluate.",
            issues=["Empty research summary."],
        )
    original = (initial_user_input or "").strip() or "(none)"
    choice = (clarifying_choice or "").strip() or "(none provided)"

    prompt = f"""Original user request:
{original}

User's clarifying choice (answers / selection after clarification):
{choice}

Deep research summary to evaluate:
{research}
"""
    result = await Runner.run(evaluator_agent, prompt)
    return result.final_output


# --- Orchestrator (session + intent + reply agent) ---


class UserResearchIntent(BaseModel):
    wants_research: bool = Field(
        description="True if the user wants web-backed research: facts, comparisons, current options, how-to needing sources."
    )
    research_topic: str = Field(
        description="Standalone research query to run; summarize the ask in one clear line. Empty if not a research request."
    )
    small_talk_reply: str = Field(
        description="If wants_research is false, a short friendly reply to the user."
    )


orchestrator_intent_agent = Agent(
    name="OrchestratorIntent",
    instructions="""Classify the user's message.
If they want research (look something up, compare products, summarize a field, recent facts), set wants_research true and set research_topic to the core question.
If they are greeting, chatting, or not asking for research, set wants_research false and give a brief small_talk_reply.""",
    model=DEFAULT_MODEL,
    output_type=UserResearchIntent,
)


class OrchestratorUserReply(BaseModel):
    message_to_user: str = Field(
        description="Single message to show the user: findings, evaluation verdict, and caveats."
    )


ORCHESTRATOR_REPLY_INSTRUCTIONS = """You are the research assistant speaking directly to the user.

You receive the original request, their clarifying choice, the research summary, and an evaluation (pass/fail plus rationale and issues).

Write one cohesive, friendly message: lead with what matters, include the research summary (you may shorten slightly), state whether the answer passed evaluation and why, and mention any caveats. Do not sound robotic."""


orchestrator_agent = Agent(
    name="ResearchOrchestrator",
    instructions=ORCHESTRATOR_REPLY_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=OrchestratorUserReply,
)


@dataclass
class OrchestratorSession:
    """Tracks multi-turn flow: idle → awaiting clarifying choice → back to idle after a run."""

    phase: Literal["idle", "awaiting_clarification"] = "idle"
    research_query: str | None = None
    clarifying_snapshot: ClarifyingQuestionsResult | None = None


def _format_clarifying_prompt(
    topic: str,
    clarifying: ClarifyingQuestionsResult,
) -> str:
    lines = [
        f"**Understood:** {clarifying.understood_so_far}",
        "",
        "Please reply with your clarifying choice — answer the questions below (or summarize constraints in your own words):",
        "",
    ]
    for i, q in enumerate(clarifying.questions, start=1):
        lines.append(f"{i}. {q.question}  \n   *Why:* {q.why_it_matters}")
        lines.append("")
    lines.append("_When you reply, I will run research and evaluation using your answers._")
    return "\n".join(lines)


async def _compose_orchestrator_reply(
    research_topic: str,
    clarifying_choice: str,
    research_summary: str,
    evaluation: ResearchEvaluation,
) -> str:
    payload = f"""Original request:
{research_topic}

User clarifying choice:
{clarifying_choice}

Research summary:
{research_summary}

Evaluation — passed: {evaluation.is_correct}
Rationale: {evaluation.rationale}
Issues: {evaluation.issues if evaluation.issues else "(none)"}
"""
    result = await Runner.run(orchestrator_agent, payload)
    return result.final_output.message_to_user


async def _run_research_pipeline(
    research_topic: str,
    clarifying_choice: str,
) -> tuple[str, ResearchEvaluation]:
    research_prompt = (
        f"User request:\n{research_topic}\n\n"
        f"Clarifying choice / constraints:\n{clarifying_choice}\n\n"
        "Answer with a concise summary that respects these constraints."
    )
    summary = await deep_research(research_prompt)
    evaluation = await evaluate_research(research_topic, clarifying_choice, summary)
    return summary, evaluation


async def orchestrator_session_step(
    session: OrchestratorSession,
    user_message: str,
) -> tuple[OrchestratorSession, str]:
    """Handle one user message: route intent, run clarify → research → evaluate, or resume after clarification."""
    text = (user_message or "").strip()
    if not text:
        return session, "Say something to continue."

    with trace("Orchestrator"):
        if session.phase == "awaiting_clarification":
            rq = session.research_query or ""
            choice = text
            summary, evaluation = await _run_research_pipeline(rq, choice)
            reply = await _compose_orchestrator_reply(rq, choice, summary, evaluation)
            return OrchestratorSession(), reply

        intent = (await Runner.run(orchestrator_intent_agent, text)).final_output
        if not intent.wants_research:
            return session, intent.small_talk_reply

        topic = (intent.research_topic or text).strip()
        if not topic:
            return session, "What topic should I research?"

        clarifying = await clarify(topic)

        if not clarifying.questions:
            summary, evaluation = await _run_research_pipeline(
                topic,
                "(No additional clarification needed.)",
            )
            reply = await _compose_orchestrator_reply(
                topic,
                "(No additional clarification needed.)",
                summary,
                evaluation,
            )
            return OrchestratorSession(), reply

        session.phase = "awaiting_clarification"
        session.research_query = topic
        session.clarifying_snapshot = clarifying
        return session, _format_clarifying_prompt(topic, clarifying)
