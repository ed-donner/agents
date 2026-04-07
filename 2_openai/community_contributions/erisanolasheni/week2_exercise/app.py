"""Gradio UI: clarifying questions, then streaming deep-research run."""

from __future__ import annotations

import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

_manager = ResearchManager()


async def get_questions(topic: str) -> str:
    topic = (topic or "").strip()
    if not topic:
        return "Enter a research topic first."
    return await _manager.clarify(topic)


async def run_research(topic: str, answers: str):
    topic = (topic or "").strip()
    if not topic:
        yield "Enter a research topic first."
        return
    async for chunk in _manager.run(topic, (answers or "").strip()):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown(
        "# Week 2 exercise — Deep research with clarification and agentic expansion\n\n"
        "1. Enter a topic and generate **three clarifying questions**.\n"
        "2. Answer them, then run the full pipeline (planner → web search → expansion agent → "
        "writer → evaluator → optional revision → email).\n"
        "_Requires API keys in `.env`; optional SendGrid for email._"
    )
    topic = gr.Textbox(label="Research topic", placeholder="e.g. Commercial uses of agentic AI in 2025")
    q_btn = gr.Button("Generate clarifying questions")
    clarify_md = gr.Markdown(label="Clarifying questions")
    answers = gr.Textbox(
        label="Your answers to the questions above",
        lines=6,
        placeholder="Answer each clarifying question in order (short paragraphs are fine).",
    )
    run_btn = gr.Button("Run deep research", variant="primary")
    report_md = gr.Markdown(label="Status and report")

    q_btn.click(fn=get_questions, inputs=topic, outputs=clarify_md)
    run_btn.click(fn=run_research, inputs=[topic, answers], outputs=report_md)

if __name__ == "__main__":
    ui.launch(inbrowser=True)
