"""
Deep Research Agent -- Gradio UI
=================================
Single-button experience:
  1. User enters a query and clicks Research (or presses Enter).
  2. The clarifier runs automatically -- questions appear in the status stream
     as scope bullets so the user knows what will be researched.
  3. The full agentic pipeline (plan -> search -> sufficiency -> write -> evaluate)
     streams every status update in real time.
  4. The final report renders in the right panel when ready.

No multi-step clicks. Everything is automatic.

PR checklist:
  - Streaming front-facing model calls (Runner.run_streamed inside ResearchManager)
  - Exception handling (try/except at every stage)
  - Bring solution to life (Gradio launch)
"""
from __future__ import annotations

import gradio as gr

import config  # must be first -- sets up the default OpenAI-compatible client
from agents import Runner
from manager import ResearchManager
from research_agents import clarifier_agent


# ---------------------------------------------------------------------------
# Single streaming function -- drives the entire UI
# ---------------------------------------------------------------------------
async def run_research(query: str):
    """
    Runs the full deep research pipeline automatically:
      1. Clarify scope (automatic, no user input needed)
      2. Plan + parallel search
      3. Sufficiency check (with optional extra search round)
      4. Write report
      5. Evaluate (with optional revision round)
      6. Hand off to email agent
    Yields (status_text, report_markdown) tuples for Gradio streaming.
    """
    if not query.strip():
        yield "Please enter a research query.", ""
        return

    status = ""
    report = ""

    # Stage 1: auto-clarify (show scope, do not block)
    status += "Analysing research scope...\n"
    yield status, report

    auto_clarifications = ""
    try:
        clarify_result = await Runner.run(clarifier_agent, query.strip())
        qs = clarify_result.final_output.questions[:3]
        summary = getattr(clarify_result.final_output, "context_summary", "")

        status += f"{summary}\n\nThis research will explore:\n"
        for q in qs:
            status += f"  - {q}\n"
        status += "\n"
        yield status, report

        auto_clarifications = "Research scope questions (auto-generated):\n" + "\n".join(
            f"- {q}" for q in qs
        )
    except Exception as exc:
        status += f"Warning: Could not auto-clarify scope: {exc}\nProceeding with original query.\n\n"
        yield status, report

    # Stage 2: full agentic research pipeline
    manager = ResearchManager()
    try:
        async for chunk in manager.run(query.strip(), auto_clarifications):
            if chunk.startswith("\n---\n"):
                report = chunk[5:]
                yield status, report
            else:
                status += chunk
                yield status, report
    except Exception as exc:
        status += f"\nError: Research failed -- {exc}\n"
        yield status, report


# ---------------------------------------------------------------------------
# Gradio layout
# ---------------------------------------------------------------------------
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="sky", secondary_hue="slate"),
    title="Deep Research Agent",
) as demo:

    gr.Markdown(
        """
# Deep Research Agent

Enter a topic and click **Research** -- the agent will automatically clarify scope,
plan and run parallel web searches, check if more research is needed, write a
detailed report, evaluate it, and email the result.

**Pipeline:** Clarify -> Plan -> Search (parallel) -> Sufficiency check -> Write -> Evaluate -> Email
"""
    )

    with gr.Row():
        # Left column: input
        with gr.Column(scale=1):
            query_box = gr.Textbox(
                label="What would you like to research?",
                placeholder="e.g. What are the latest advances in fusion energy?",
                lines=4,
            )
            research_btn = gr.Button("Run Research", variant="primary", size="lg")
            gr.Markdown(
                "_Press Enter or click Run Research. Everything runs automatically._",
                elem_classes=["hint"],
            )

        # Right column: live output
        with gr.Column(scale=2):
            with gr.Tab("Live status"):
                status_box = gr.Textbox(
                    label="",
                    lines=20,
                    interactive=False,
                    show_copy_button=True,
                    placeholder="Status updates will appear here as the agent works...",
                )
            with gr.Tab("Final report"):
                report_box = gr.Markdown(
                    value="The report will appear here when the agent finishes writing."
                )

    # Event wiring
    research_btn.click(
        fn=run_research,
        inputs=[query_box],
        outputs=[status_box, report_box],
    )
    query_box.submit(
        fn=run_research,
        inputs=[query_box],
        outputs=[status_box, report_box],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
