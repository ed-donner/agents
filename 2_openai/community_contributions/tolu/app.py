#!/usr/bin/env python3
"""Gradio UI for education policy deep research."""

from __future__ import annotations
import os
import gradio as gr
from dotenv import load_dotenv
from research_manager import PolicyResearchManager

load_dotenv(override=True)

async def run_policy_research(query: str):
    if not query or not query.strip():
        yield "Enter an education policy question."
        return
    if not os.environ.get("OPENAI_API_KEY"):
        yield "Set `OPENAI_API_KEY` in your environment or repo-root `.env`."
        return

    lines: list[str] = []
    async for chunk in PolicyResearchManager().run(query.strip()):
        if chunk.startswith("[status] "):
            lines.append(chunk.removeprefix("[status] "))
        else:
            lines.append("---\n\n## Policy brief\n\n" + chunk)
        yield "\n\n".join(lines)

with gr.Blocks(title="Education Policy Deep Research") as ui:
    gr.Markdown(
        "# Education Policy Deep Research\n\n"
        "Planner → parallel web search → structured markdown brief. "
        "**Not legal advice**—verify with official sources.\n\n"
        "Course materials: [ed-donner/agents](https://github.com/ed-donner/agents)."
    )
    query_box = gr.Textbox(
        label="Education policy question",
        placeholder="e.g. How are Finland and Singapore approaching early childhood education reforms?",
        lines=3,
    )
    run_btn = gr.Button("Run research", variant="primary")
    output = gr.Markdown(label="Status & brief")

    run_btn.click(fn=run_policy_research, inputs=query_box, outputs=output)
    query_box.submit(fn=run_policy_research, inputs=query_box, outputs=output)

if __name__ == "__main__":
    ui.launch(inbrowser=True)