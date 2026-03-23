"""
Gradio UI for the multi-agent course creation system.

From the agents repo root:

  uv run python 2_openai/community_contributions/makinda/week2_exercise/app.py

Optional distributed mode (start a2a_services.py for each role first):

  USE_A2A_REMOTE=1 uv run python 2_openai/community_contributions/makinda/week2_exercise/app.py

Requires OPENAI_API_KEY and SERPER_API_KEY in the environment (or .env).
"""

from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MODEL, USE_A2A_REMOTE  
from orchestrator import format_log_lines, run_course_pipeline  


async def generate_course(topic: str) -> tuple[str, str]:
    topic = (topic or "").strip()
    if not topic:
        return "Please enter a topic or learning goal.", ""

    log: list[str] = []
    try:
        markdown = await run_course_pipeline(topic, status_log=log)
        header = (
            f"*Model: `{MODEL}` · "
            f"Mode: `{'remote A2A stubs' if USE_A2A_REMOTE else 'in-process'}`*\n\n"
        )
        return header + markdown, format_log_lines(log)
    except Exception as exc:  
        log.append(f"[error] {exc!r}")
        return f"Run failed: {exc}", format_log_lines(log)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Week 2 — Course creation agents") as demo:
        gr.Markdown(
            "## Multi-agent course creation\n"
            "Researcher (Serper search) → Judge (structured pass/fail) → loop → "
            "Content builder (Markdown course). Uses **OpenAI Agents SDK** with `gpt-4o-mini` by default."
        )
        topic = gr.Textbox(
            label="Topic / learning goal",
            placeholder="e.g. Introduction to vector databases for RAG",
            lines=2,
        )
        run_btn = gr.Button("Generate course", variant="primary")
        course_out = gr.Markdown(label="Course (Markdown)")
        log_out = gr.Textbox(label="Run log", lines=14, max_lines=24)

        run_btn.click(fn=generate_course, inputs=[topic], outputs=[course_out, log_out])

    return demo


if __name__ == "__main__":
    build_ui().launch()
