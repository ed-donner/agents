"""Gradio entrypoint: Question + main Markdown + separate progress log (plan.md)."""

from __future__ import annotations

import asyncio
import sys

import config  # noqa: F401 - load dotenv before other app imports

import gradio as gr

from env_validate import format_env_error, list_missing_required_env
from flow import advance_session_stream
from models import ResearchSession, append_status_line

IDLE_MAIN_MD = (
    "*Ready.* Enter a research question and click **Submit** to run triage. "
    "If the query is vague, you will be asked follow-up questions in this panel."
)


def _format_progress(session: ResearchSession) -> str:
    if not session.progress_log:
        return ""
    return "\n".join(session.progress_log)


def _markdown_evaluator_rejection(session: ResearchSession) -> str:
    """Final evaluator failure: last report + structured sections (plan.md §13 O6)."""
    r = session.report
    ev = session.last_evaluation
    assert r is not None and ev is not None
    body = (r.markdown_report or "").strip()
    summ = (r.summary or "").strip()
    core = f"{body}\n\n---\n\n### Summary\n\n{summ}" if summ else body
    err_line = (session.last_error or "").strip()
    gaps_md = "\n".join(f"- {g}" for g in ev.gaps) if ev.gaps else "_(none listed)_"
    sug_md = (
        "\n".join(f"- `{s}`" for s in ev.suggested_searches)
        if ev.suggested_searches
        else "_(none listed)_"
    )
    return (
        f"{core}\n\n## Evaluator\n\n"
        f"_{err_line}_\n\n"
        f"### Gaps\n\n{gaps_md}\n\n"
        f"### Suggested searches\n\n{sug_md}\n"
    )


def _main_markdown_for_session(session: ResearchSession) -> str:
    if session.phase == "error":
        if session.last_evaluation is not None and session.report is not None:
            return _markdown_evaluator_rejection(session)
        err = session.last_error or "Unknown error."
        ctx = session.user_question.strip() or "_(no text)_"
        return f"## Error\n\n{err}\n\n### Context\n\n{ctx}"

    if session.phase == "researching":
        if session.report is not None:
            r = session.report
            body = (r.markdown_report or "").strip()
            summ = (r.summary or "").strip()
            core = f"{body}\n\n---\n\n### Summary\n\n{summ}" if summ else body
            return f"{core}\n\n---\n\n*Draft - evaluation in progress or retrying…*"
        return (
            "### Working…\n\n"
            "_Research pipeline running - see **Progress / status** below._"
        )

    if session.phase == "awaiting_clarification":
        qs = session.pending_clarification_questions or []
        lines = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(qs))
        return (
            "### Clarification needed\n\n"
            f"{lines}\n\n"
            "*Enter your answers in the field below (one line per question or one short paragraph), "
            "then click **Submit / Continue**.*"
        )

    if session.phase == "done" and session.report is not None:
        r = session.report
        body = (r.markdown_report or "").strip()
        summ = (r.summary or "").strip()
        if summ:
            return f"{body}\n\n---\n\n### Summary\n\n{summ}"
        return body or "*_(Empty report.)_*"

    if session.user_question.strip():
        return (
            f"### Current question\n\n{session.user_question.strip()}\n\n"
            f"{IDLE_MAIN_MD}"
        )
    return IDLE_MAIN_MD


def _question_component_update(
    session: ResearchSession,
    *,
    clear_value: bool,
) -> dict:
    if session.phase == "awaiting_clarification":
        upd = gr.update(
            label="Your answers",
            placeholder=(
                "Answer the questions above (one line per question or one paragraph)…"
            ),
        )
        if isinstance(upd, dict) and clear_value:
            upd["value"] = ""
        return upd
    upd = gr.update(
        label="Question",
        placeholder="Enter your research question…",
    )
    if isinstance(upd, dict) and clear_value:
        upd["value"] = ""
    return upd


def handle_reset() -> tuple[ResearchSession, str, str, str]:
    session = ResearchSession()
    return session, IDLE_MAIN_MD, "", ""


def _submit_outputs(session: ResearchSession, clear_box: bool) -> tuple:
    return (
        session,
        _main_markdown_for_session(session),
        _format_progress(session),
        _question_component_update(session, clear_value=clear_box),
    )


async def handle_submit(
    question: str,
    session: ResearchSession,
):
    """Async **generator**: each ``yield`` pushes Markdown + progress so the UI does not freeze."""
    if not isinstance(session, ResearchSession):
        session = ResearchSession()

    append_status_line(session.progress_log, "submit: start")
    clear_box = False
    await asyncio.sleep(0)
    yield _submit_outputs(session, clear_box)

    async for clear_box in advance_session_stream(session, question or ""):
        await asyncio.sleep(0)
        yield _submit_outputs(session, clear_box)

    append_status_line(session.progress_log, "submit: end")
    await asyncio.sleep(0)
    yield _submit_outputs(session, clear_box)


def build_app() -> gr.Blocks:
    missing = list_missing_required_env()
    if missing:
        err = format_env_error(missing)
        print(err.replace("**", ""), file=sys.stderr)
        with gr.Blocks(title="Deep research - configuration error") as demo:
            gr.Markdown("# Deep research (v1)")
            gr.Markdown(err)
        return demo

    with gr.Blocks(title="Deep research") as demo:
        gr.Markdown("# Deep research (v1)")

        session_state = gr.State(ResearchSession())

        with gr.Row():
            question = gr.Textbox(
                label="Question",
                placeholder="Enter your research question…",
                lines=3,
                scale=4,
            )
        with gr.Row():
            submit_btn = gr.Button("Submit / Continue", variant="primary")
            reset_btn = gr.Button("Reset")

        main_out = gr.Markdown(value=IDLE_MAIN_MD)
        progress_out = gr.Textbox(
            label="Progress / status",
            value="",
            lines=14,
            max_lines=24,
            interactive=False,
            elem_classes=["progress-status"],
        )

        submit_btn.click(
            fn=handle_submit,
            inputs=[question, session_state],
            outputs=[session_state, main_out, progress_out, question],
        )
        reset_btn.click(
            fn=handle_reset,
            inputs=None,
            outputs=[session_state, main_out, progress_out, question],
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
