from __future__ import annotations

import asyncio
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

# core.orchestrator must be imported first to avoid a circular import:
# agents.clarifier → core.state → core/__init__ → core.orchestrator → agents.clarifier
from core.orchestrator import DeepResearchRuntime  # noqa: E402
from core.state import ClarificationQuestions
from agents import Runner
from agents.clarifier import clarifier_agent


def _load_env() -> None:
    load_dotenv(override=True)
    repo_root = Path(__file__).resolve().parents[3]
    fallback_env = repo_root / ".env"
    if fallback_env.exists():
        load_dotenv(fallback_env, override=False)


_load_env()

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Lora:ital,wght@0,400;0,500;1,400;1,500&family=IBM+Plex+Mono:wght@300;400&display=swap');

/* ── Base ────────────────────────────────────────────────── */
body,
.gradio-container {
    background: #f6f2eb !important;
    color: #1c1714 !important;
    font-family: 'Lora', Georgia, serif !important;
}

.gradio-container {
    max-width: 740px !important;
    margin: 0 auto !important;
    padding: 64px 32px 100px !important;
}

footer { display: none !important; }

/* ── Title block ─────────────────────────────────────────── */
#rh-title h1 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 3rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.01em !important;
    color: #1c1714 !important;
    margin: 0 0 6px !important;
    line-height: 1.05 !important;
}

#rh-subtitle p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    color: #a09890 !important;
    margin: 0 0 52px !important;
}

/* ── Horizontal rules ────────────────────────────────────── */
.rh-rule {
    border: none !important;
    border-top: 1px solid #cec9c0 !important;
    margin: 40px 0 32px !important;
}

/* ── Section eyebrow labels ──────────────────────────────── */
.rh-eyebrow p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.63rem !important;
    letter-spacing: 0.24em !important;
    text-transform: uppercase !important;
    color: #8a1c2e !important;
    margin: 0 0 22px !important;
}

/* ── Status line ─────────────────────────────────────────── */
#rh-status p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 300 !important;
    color: #8a1c2e !important;
    margin: 10px 0 0 !important;
    min-height: 20px !important;
}

/* ── All textareas / inputs ──────────────────────────────── */
textarea,
input[type="text"] {
    background: #f0ece3 !important;
    border: none !important;
    border-bottom: 1px solid #cec9c0 !important;
    border-radius: 0 !important;
    color: #1c1714 !important;
    font-family: 'Lora', Georgia, serif !important;
    font-size: 1.08rem !important;
    padding: 10px 4px !important;
    resize: none !important;
    box-shadow: none !important;
    transition: border-color 0.18s ease !important;
}

textarea:focus,
input[type="text"]:focus {
    border-bottom-color: #8a1c2e !important;
    outline: none !important;
    box-shadow: none !important;
    background: #ede9e0 !important;
}

/* ── Question labels (01 / 02 / 03) ─────────────────────── */
#rh-q1 label span,
#rh-q2 label span,
#rh-q3 label span {
    font-family: 'Lora', Georgia, serif !important;
    font-size: 0.98rem !important;
    font-style: italic !important;
    font-weight: 400 !important;
    color: #5a534e !important;
    display: block !important;
    padding-bottom: 4px !important;
}

#rh-q1 label::before { content: "01"; font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; color: #a09890; display: block; margin-bottom: 6px; }
#rh-q2 label::before { content: "02"; font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; color: #a09890; display: block; margin-bottom: 6px; }
#rh-q3 label::before { content: "03"; font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; color: #a09890; display: block; margin-bottom: 6px; }

/* ── Buttons ─────────────────────────────────────────────── */
button.primary {
    background: #8a1c2e !important;
    color: #f6f2eb !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 13px 32px !important;
    cursor: pointer !important;
    transition: background 0.18s ease !important;
}

button.primary:hover:not(:disabled) {
    background: #a82337 !important;
}

button.primary:disabled {
    background: #c8b8b8 !important;
    cursor: default !important;
}

button.secondary {
    background: transparent !important;
    color: #a09890 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border: 1px solid #cec9c0 !important;
    border-radius: 0 !important;
    padding: 11px 28px !important;
    cursor: pointer !important;
    transition: border-color 0.18s ease, color 0.18s ease !important;
}

button.secondary:hover {
    border-color: #a09890 !important;
    color: #5a534e !important;
}

/* ── Progress log ────────────────────────────────────────── */
#rh-log textarea {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    font-weight: 300 !important;
    line-height: 1.8 !important;
    color: #6a635e !important;
    background: #ede9e0 !important;
    border: none !important;
    border-left: 2px solid #cec9c0 !important;
    padding: 16px 20px !important;
}

/* ── Report ──────────────────────────────────────────────── */
#rh-report {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

#rh-report h1 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 2.1rem !important;
    font-weight: 400 !important;
    color: #1c1714 !important;
    margin: 0 0 4px !important;
    padding-bottom: 16px !important;
    border-bottom: 1px solid #cec9c0 !important;
}

#rh-report h2 {
    font-family: 'Lora', Georgia, serif !important;
    font-size: 0.78rem !important;
    font-weight: 400 !important;
    font-style: normal !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #8a1c2e !important;
    margin: 36px 0 12px !important;
}

#rh-report p {
    font-size: 1.02rem !important;
    line-height: 1.82 !important;
    color: #2e2a27 !important;
    margin-bottom: 14px !important;
}

#rh-report li {
    font-size: 1rem !important;
    line-height: 1.75 !important;
    color: #2e2a27 !important;
    margin-bottom: 7px !important;
    padding-left: 4px !important;
}

/* ── Misc Gradio chrome removal ──────────────────────────── */
.block, .form, .gap, .wrap, .svelte-1ed2p3z {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.gradio-row { gap: 12px !important; }
"""


async def fetch_questions(query: str):
    """Stage 1 — show working state, run clarifier, surface questions."""
    if not query.strip():
        yield (gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update())
        return

    # Immediate feedback — show status, disable button
    yield (
        gr.update(value="Generating your questions...", visible=True),
        gr.update(interactive=False),
        gr.update(visible=False),
        gr.update(),
        gr.update(),
        gr.update(),
    )

    result = await Runner.run(clarifier_agent, query.strip())
    questions = result.final_output_as(ClarificationQuestions).questions

    yield (
        gr.update(value="", visible=False),
        gr.update(interactive=True),
        gr.update(visible=True),
        gr.update(label=questions[0], value=""),
        gr.update(label=questions[1], value=""),
        gr.update(label=questions[2], value=""),
    )


async def run_research(query: str, a1: str, a2: str, a3: str):
    """Stage 2 — run the full research loop and stream events."""
    answers = [
        a1.strip() or "No additional preference.",
        a2.strip() or "No additional preference.",
        a3.strip() or "No additional preference.",
    ]

    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    def event_handler(msg: str) -> None:
        queue.put_nowait(("msg", msg))

    def answer_provider(_questions: list[str]) -> list[str]:
        return answers

    async def _research_task() -> None:
        runtime = DeepResearchRuntime()
        state = await runtime.run(
            query=query,
            answer_provider=answer_provider,
            event_handler=event_handler,
        )
        queue.put_nowait(("done", state))

    asyncio.create_task(_research_task())

    log_lines: list[str] = ["›  Starting research..."]

    # Reveal progress immediately with initial text
    yield (
        gr.update(visible=True),
        "\n".join(log_lines),
        gr.update(visible=False),
        "",
    )

    while True:
        kind, payload = await queue.get()

        if kind == "done":
            state = payload
            break

        log_lines.append(f"›  {payload}")
        yield (
            gr.update(),
            "\n".join(log_lines),
            gr.update(visible=False),
            "",
        )

    log_lines.append("›  Done.")

    if state.final_report:
        yield (
            gr.update(),
            "\n".join(log_lines),
            gr.update(visible=True),
            state.final_report.as_markdown(),
        )
    else:
        log_lines.append("›  No report was generated.")
        yield (
            gr.update(),
            "\n".join(log_lines),
            gr.update(visible=False),
            "",
        )


def reset_ui():
    return (
        gr.update(value=""),
        gr.update(value="", visible=False),
        gr.update(interactive=True),
        gr.update(visible=False),
        gr.update(value="", label=""),
        gr.update(value="", label=""),
        gr.update(value="", label=""),
        gr.update(visible=False),
        "",
        gr.update(visible=False),
        "",
    )


with gr.Blocks(css=_CSS, title="Deep Research") as app:

    # ── Header ────────────────────────────────────────────────
    gr.Markdown("# Deep Research", elem_id="rh-title")
    gr.Markdown("Agentic · Multi-pass · Source-grounded", elem_id="rh-subtitle")

    # ── Phase 1 — Query ───────────────────────────────────────
    query_input = gr.Textbox(
        placeholder="What would you like to research?",
        lines=2,
        show_label=False,
        autofocus=True,
    )
    with gr.Row():
        continue_btn = gr.Button("Continue →", variant="primary")
        reset_btn = gr.Button("Reset", variant="secondary")

    status_md = gr.Markdown("", elem_id="rh-status", visible=False)

    # ── Phase 2 — Clarification ───────────────────────────────
    with gr.Column(visible=False) as clarify_group:
        gr.HTML('<hr class="rh-rule" />')
        gr.Markdown("A few questions to sharpen the brief", elem_classes=["rh-eyebrow"])
        a1 = gr.Textbox(label="", lines=2, elem_id="rh-q1")
        a2 = gr.Textbox(label="", lines=2, elem_id="rh-q2")
        a3 = gr.Textbox(label="", lines=2, elem_id="rh-q3")
        research_btn = gr.Button("Research →", variant="primary")

    # ── Phase 3 — Progress ────────────────────────────────────
    with gr.Column(visible=False) as progress_group:
        gr.HTML('<hr class="rh-rule" />')
        gr.Markdown("Research log", elem_classes=["rh-eyebrow"])
        log_box = gr.Textbox(
            lines=10,
            show_label=False,
            interactive=False,
            elem_id="rh-log",
        )

    # ── Phase 4 — Report ──────────────────────────────────────
    with gr.Column(visible=False) as report_group:
        gr.HTML('<hr class="rh-rule" />')
        gr.Markdown("Final report", elem_classes=["rh-eyebrow"])
        report_md = gr.Markdown(elem_id="rh-report")

    # ── Wiring ────────────────────────────────────────────────
    continue_btn.click(
        fn=fetch_questions,
        inputs=[query_input],
        outputs=[status_md, continue_btn, clarify_group, a1, a2, a3],
    )

    research_btn.click(
        fn=run_research,
        inputs=[query_input, a1, a2, a3],
        outputs=[progress_group, log_box, report_group, report_md],
    )

    reset_btn.click(
        fn=reset_ui,
        inputs=[],
        outputs=[
            query_input, status_md, continue_btn,
            clarify_group, a1, a2, a3,
            progress_group, log_box,
            report_group, report_md,
        ],
    )


if __name__ == "__main__":
    app.launch()
