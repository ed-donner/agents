#!/usr/bin/env python3
"""Gradio UI for policy deep research (Week 2 OpenAI Agents SDK pattern).

Upstream course repo: https://github.com/ed-donner/agents

Run from this directory (course venv active):
  python app.py
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

from research_manager import PolicyResearchManager

load_dotenv(override=True)


async def run_policy_research(query: str):
    if not query or not query.strip():
        yield "Enter a policy question."
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


with gr.Blocks(
    theme=gr.themes.Default(primary_hue="slate"),
    title="Policy deep research",
) as ui:
    gr.Markdown(
        "# Government & public policy deep research\n\n"
        "Planner → parallel web search → structured markdown brief. "
        "**Not legal advice**—verify with official sources and qualified professionals.\n\n"
        "Course materials: [ed-donner/agents](https://github.com/ed-donner/agents)."
    )
    query_box = gr.Textbox(
        label="Policy research question",
        placeholder="e.g. What changed in UK online safety duties for platforms in the last two years?",
        lines=3,
    )
    run_btn = gr.Button("Run research", variant="primary")
    output = gr.Markdown(label="Status & brief")

    run_btn.click(fn=run_policy_research, inputs=query_box, outputs=output)
    query_box.submit(fn=run_policy_research, inputs=query_box, outputs=output)

if __name__ == "__main__":
    ui.launch(inbrowser=True)
