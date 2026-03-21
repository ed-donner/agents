"""Python-controlled triage -> clarification (Phase E) + research + evaluator (Phase F + I).

Progress lines are appended here so Gradio can ``yield`` after each step
(see ``advance_session_stream``).
"""

from __future__ import annotations

import asyncio
import config

from pushover_client import send_pushover_completion_notice

from clarifier import run_clarifier
from evaluator import run_evaluator
from merge import merge_clarifications
from models import (
    EvaluationResult,
    ResearchData,
    ResearchSession,
    SearchItem,
    SearchPlan,
    append_status_line,
)
from planner import run_planner
from report import run_report
from research import run_research
from triage import run_triage


async def _build_retry_search_plan(
    canonical_question: str,
    ev: EvaluationResult,
) -> SearchPlan:
    """Supplemental searches after a failed evaluation."""
    trimmed = [s.strip() for s in ev.suggested_searches if s.strip()]
    if trimmed:
        items = [
            SearchItem(
                query=q[:500],
                reason="Evaluator-suggested search to address report gaps.",
            )
            for q in trimmed[: config.DEFAULT_PHRASES_COUNT]
        ]
        return SearchPlan(searches=items)
    gap_block = (
        "\n\n## Gaps the previous draft must address\n"
        + "\n".join(f"- {g}" for g in ev.gaps)
        if ev.gaps
        else ""
    )
    return await run_planner(
        canonical_question + gap_block,
        config.DEFAULT_PHRASES_COUNT,
    )


async def _research_chain_stream(
    session: ResearchSession,
    clear_answers_field: bool,
):
    """Planner -> research -> report -> evaluator, with bounded retries (plan.md Phase I)."""
    session.phase = "researching"
    session.last_evaluation = None
    research_accum: ResearchData | None = None
    last_eval: EvaluationResult | None = None
    total_rounds = config.MAX_EVALUATOR_RETRIES + 1

    try:
        for round_idx in range(total_rounds):
            append_status_line(
                session.progress_log,
                f"pipeline: round {round_idx + 1}/{total_rounds}",
            )
            yield clear_answers_field

            if round_idx == 0:
                append_status_line(session.progress_log, "planner: start")
                yield clear_answers_field
                plan = await run_planner(
                    session.user_question,
                    config.DEFAULT_PHRASES_COUNT,
                )
                append_status_line(session.progress_log, "planner: end")
                yield clear_answers_field
            else:
                assert last_eval is not None
                append_status_line(
                    session.progress_log,
                    f"evaluator: retry {round_idx}/{config.MAX_EVALUATOR_RETRIES} - supplemental plan",
                )
                yield clear_answers_field
                plan = await _build_retry_search_plan(
                    session.user_question,
                    last_eval,
                )
                append_status_line(
                    session.progress_log,
                    "retry: supplemental search plan ready",
                )
                yield clear_answers_field

            session.search_plan = plan

            append_status_line(session.progress_log, "research: start")
            yield clear_answers_field
            research_delta = await run_research(plan)
            if research_accum is None:
                research_accum = research_delta
            else:
                research_accum = ResearchData(
                    results=list(research_accum.results) + list(research_delta.results),
                )
            session.research_data = research_accum
            append_status_line(session.progress_log, "research: end")
            yield clear_answers_field

            append_status_line(session.progress_log, "report: start")
            yield clear_answers_field
            report = await run_report(session.user_question, research_accum)
            session.report = report
            append_status_line(session.progress_log, "report: end")
            yield clear_answers_field

            append_status_line(session.progress_log, "evaluator: start")
            yield clear_answers_field
            ev = await run_evaluator(
                session.user_question,
                report,
                research_accum,
            )
            if config.EVALUATOR_DEBUG_ALWAYS_FAIL:
                append_status_line(
                    session.progress_log,
                    "evaluator: DEBUG - EVALUATOR_DEBUG_ALWAYS_FAIL (forced fail; unset for production)",
                )
                ev = EvaluationResult(
                    passes=False,
                    gaps=[
                        "Debug: `EVALUATOR_DEBUG_ALWAYS_FAIL` is set. "
                        "Unset it to use the real evaluator."
                    ],
                    suggested_searches=["debug supplemental probe"],
                )
            elif config.EVALUATOR_DEBUG_FAIL_ONCE and round_idx == 0:
                append_status_line(
                    session.progress_log,
                    "evaluator: DEBUG - EVALUATOR_DEBUG_FAIL_ONCE (first round only)",
                )
                ev = EvaluationResult(
                    passes=False,
                    gaps=[
                        "Debug: simulated first-round failure; later rounds use the real verdict."
                    ],
                    suggested_searches=["debug retry search"],
                )
            append_status_line(
                session.progress_log,
                f"evaluator: end - {'pass' if ev.passes else 'fail'}",
            )
            yield clear_answers_field

            if ev.passes:
                session.phase = "done"
                session.last_error = None
                session.last_evaluation = None
                append_status_line(
                    session.progress_log,
                    "pipeline: evaluator approved - report ready",
                )
                yield clear_answers_field

                append_status_line(session.progress_log, "pushover: sending notification")
                yield clear_answers_field
                ok, perr = await asyncio.to_thread(send_pushover_completion_notice)
                if ok:
                    append_status_line(
                        session.progress_log,
                        "pushover: notification sent",
                    )
                else:
                    append_status_line(
                        session.progress_log,
                        f"pushover: failed - {perr}",
                    )
                yield clear_answers_field
                return

            if round_idx >= total_rounds - 1:
                session.phase = "error"
                session.last_error = (
                    "The evaluator did not approve the report after the maximum "
                    f"number of tries ({total_rounds})."
                )
                session.last_evaluation = ev
                append_status_line(
                    session.progress_log,
                    "evaluator: max retries exceeded - stopping",
                )
                yield clear_answers_field
                return

            last_eval = ev
            append_status_line(
                session.progress_log,
                "evaluator: report needs improvement - running supplemental research",
            )
            yield clear_answers_field

    except Exception as exc:  # noqa: BLE001 - surface any agent/API failure to UI
        session.phase = "error"
        session.last_error = str(exc) or type(exc).__name__
        session.last_evaluation = None
        append_status_line(
            session.progress_log,
            f"pipeline: failed - {session.last_error}",
        )
        yield clear_answers_field


async def advance_session_stream(
    session: ResearchSession,
    text_input: str,
):
    """Advance session; **yield** ``clear_answers_field`` after each progress/UI step."""
    clear_answers_field = False

    if session.phase == "error":
        append_status_line(
            session.progress_log,
            "submit: session is in error state - use Reset to start over",
        )
        yield clear_answers_field
        return

    if session.phase == "done":
        append_status_line(
            session.progress_log,
            "submit: research finished - use Reset for a new question",
        )
        yield clear_answers_field
        return

    if session.triage_complete:
        append_status_line(
            session.progress_log,
            "submit: triage already complete; use Reset for a new question",
        )
        yield clear_answers_field
        return

    from_clarification = session.phase == "awaiting_clarification"

    if from_clarification:
        qs = session.pending_clarification_questions or []
        merged = merge_clarifications(session.user_question, qs, text_input)
        session.user_question = merged
        session.pending_clarification_questions = None
        session.phase = "idle"
        clear_answers_field = True
        append_status_line(
            session.progress_log,
            "clarification: merged answers into canonical question",
        )
        yield clear_answers_field

    if session.phase != "idle":
        return

    if session.triage_runs_completed == 0 and not from_clarification:
        q = (text_input or "").strip()
        if not q:
            append_status_line(session.progress_log, "submit: enter a question first")
            yield clear_answers_field
            return
        session.user_question = q

    append_status_line(session.progress_log, "triage: start")
    yield clear_answers_field
    t = await run_triage(session.user_question)
    session.triage_history.append(t)
    session.triage_runs_completed += 1
    append_status_line(session.progress_log, "triage: end")
    yield clear_answers_field

    if not t.is_ambiguous:
        session.triage_complete = True
        session.last_error = None
        append_status_line(session.progress_log, "triage: query accepted as clear")
        yield clear_answers_field
        async for c in _research_chain_stream(session, clear_answers_field):
            yield c
        return

    if session.triage_runs_completed >= config.MAX_TRIAGE_ROUNDS:
        session.phase = "error"
        session.last_error = (
            "The query remained ambiguous after the maximum number of "
            f"triage passes ({config.MAX_TRIAGE_ROUNDS})."
        )
        append_status_line(session.progress_log, "triage: max rounds exceeded - stopping")
        yield clear_answers_field
        return

    append_status_line(session.progress_log, "clarifier: start")
    yield clear_answers_field
    questions = await run_clarifier(session.user_question, t.what_is_ambiguous)
    append_status_line(session.progress_log, "clarifier: end")
    session.pending_clarification_questions = questions
    session.phase = "awaiting_clarification"
    yield clear_answers_field


async def advance_session(session: ResearchSession, text_input: str) -> bool:
    """Same as :func:`advance_session_stream` but runs to completion (tests, non-UI)."""
    clear_answers_field = False
    async for clear_answers_field in advance_session_stream(session, text_input):
        pass
    return clear_answers_field
