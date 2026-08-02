"""
app.py — Gradio UI for the Deep Research Agent.

Run with:  python app.py
Or launch via the notebook.

Two-phase flow:
  Phase 1 — "Get Scope Questions": runs the clarifier, shows 3 questions.
             The user edits/selects one and optionally adds more context.
  Phase 2 — "Start Research": streams the full pipeline live.

Sessions are isolated per user (unique thread_id in gr.State).
SQLite memory persists sessions across restarts — users can resume by ID.
"""
from __future__ import annotations

import asyncio
import uuid

import gradio as gr

from agent import (
    PROVIDER,
    _LIMITS,
    _cfg,
    check_query_safety,
    load_session,
    run_clarifier,
    stream_research,
    validate_inputs,
)

import nest_asyncio
nest_asyncio.apply()


with gr.Blocks(title="Deep Research Agent") as demo:
    gr.Markdown(
        f"# Deep Research Agent\n"
        f"Provider: **{PROVIDER}** | Model: **{_cfg['model']}**\n\n"
        "Enter a research topic. The agent clarifies scope, runs parallel web searches, "
        "checks sufficiency, writes and evaluates a report, then emails it.\n\n"
        "**Pipeline:** Clarify → Plan → Search → Sufficiency → Write → Evaluate → Email"
    )

    # gr.State is per-browser-session — different users get different values.
    # Initialised as "" because passing a lambda to gr.State causes Gradio to store
    # the function object itself rather than calling it, which produces the display
    # "<function <lambda> at 0x...>". The real UUID is generated in demo.load below.
    thread_state    = gr.State("")
    questions_state = gr.State([])

    # Session management
    with gr.Row():
        session_label = gr.Textbox(
            label="Your session ID (copy to resume later)",
            interactive=False, scale=3,
        )
        resume_box = gr.Textbox(
            label="Resume a previous session",
            placeholder="Paste a session ID here", scale=3,
        )
        resume_btn = gr.Button("Load session", scale=1)

    # Research query input
    with gr.Row():
        query_box   = gr.Textbox(
            label="Research topic",
            placeholder="e.g. What are the latest advances in fusion energy?",
            info=f"10–{_LIMITS['query'][1]} characters",
            lines=2,
        )
        clarify_btn = gr.Button("Get Scope Questions", variant="secondary")

    # Clarification panel — revealed after scope questions are generated
    with gr.Group(visible=False) as clarify_group:
        gr.Markdown("### Scope — click a question to select it, then edit or add context below")
        question_radio = gr.Radio(
            label="Select a scoping question",
            choices=[],
            interactive=True,
        )
        clarification_box = gr.Textbox(
            label="Your clarification (selected question appears here — edit freely)",
            placeholder="e.g. Focus on tokamak advances in the past 2 years",
            info=f"max {_LIMITS['clarification'][1]} characters",
            lines=2,
        )
        extra_context_box = gr.Textbox(
            label="Additional context (optional)",
            placeholder="e.g. Include commercial projects and recent government funding",
            info=f"max {_LIMITS['extra_context'][1]} characters",
            lines=2,
        )
        research_btn = gr.Button("Start Research", variant="primary", size="lg")

    # Status panel
    with gr.Row():
        status_box = gr.Textbox(
            label="Pipeline status", lines=8, interactive=False,
            placeholder="Status updates will appear here as the pipeline runs...",
        )

    # Results
    with gr.Row():
        with gr.Column(scale=3):
            report_box = gr.Markdown("The report will stream here as the writer works...")
        with gr.Column(scale=1):
            score_box = gr.Textbox(label="Evaluator score", interactive=False)
            email_box = gr.Textbox(label="Email status",    interactive=False)

    # ── Event handlers ─────────────────────────────────────────────────────────

    def show_session(thread):
        # If state is empty (first page load), generate a fresh UUID.
        # Return it to BOTH outputs so the display and the state stay in sync.
        if not thread:
            thread = str(uuid.uuid4())
        return thread, thread

    demo.load(show_session, inputs=[thread_state], outputs=[session_label, thread_state])

    async def do_resume(resume_id):
        if not resume_id.strip():
            return "Please paste a session ID.", "", ""
        report, score = await load_session(resume_id)
        return report, score, ""

    resume_btn.click(
        do_resume,
        inputs=[resume_box],
        outputs=[report_box, score_box, email_box],
    )

    async def do_clarify(query, thread):
        if not query.strip():
            return gr.update(), gr.update(), "", [], thread
        # Length validation — checked before the LLM safety call to avoid wasting tokens
        valid, length_error = validate_inputs(query)
        if not valid:
            return (
                gr.update(visible=True),
                gr.update(choices=[], value=None),
                length_error, [], thread,
            )
        # Input guardrail — runs synchronously in a thread to avoid blocking
        safety = await asyncio.to_thread(check_query_safety, query.strip())
        if not safety.is_safe:
            return (
                gr.update(visible=True),
                gr.update(choices=[], value=None),
                f"Query blocked by safety check: {safety.reason}",
                [], thread,
            )
        try:
            questions, summary = await run_clarifier(query.strip())
            choices    = [f"{i+1}. {q}" for i, q in enumerate(questions)]
            new_thread = str(uuid.uuid4())
            return (
                gr.update(visible=True),
                gr.update(choices=choices, value=choices[0] if choices else None),
                questions[0] if questions else "",
                questions,
                new_thread,
            )
        except Exception as exc:
            return gr.update(visible=True), gr.update(choices=[], value=None), f"Clarifier error: {exc}", [], thread

    def on_question_select(selected):
        """When user clicks a radio option, strip the leading number and copy to clarification box."""
        if not selected:
            return ""
        # Remove leading "1. " / "2. " / "3. " prefix
        parts = selected.split(". ", 1)
        return parts[1] if len(parts) > 1 else selected

    question_radio.change(on_question_select, inputs=[question_radio], outputs=[clarification_box])

    _clarify_outputs = [clarify_group, question_radio, clarification_box, questions_state, thread_state]
    clarify_btn.click(do_clarify, inputs=[query_box, thread_state], outputs=_clarify_outputs)
    query_box.submit(do_clarify,  inputs=[query_box, thread_state], outputs=_clarify_outputs)

    async def do_research(query, clarification, extra_context, thread):
        if not query.strip():
            yield "Please enter a research topic.", "", "", ""
            return
        # Length validation on all three fields before starting the pipeline
        valid, length_error = validate_inputs(query, clarification, extra_context)
        if not valid:
            yield length_error, "", "", ""
            return
        full_clarification = clarification.strip()
        if extra_context.strip():
            full_clarification += f"\n\nAdditional context: {extra_context.strip()}"
        async for status, report, score, email in stream_research(query, full_clarification, thread):
            yield status, report, score, email

    research_btn.click(
        do_research,
        inputs=[query_box, clarification_box, extra_context_box, thread_state],
        outputs=[status_box, report_box, score_box, email_box],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
