"""Gradio app for the ARES Research System."""

import logging
import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from ares_agents import architect_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ares-app")
DEFAULT_EMAIL = "gasmyrmougang@gmail.com"


async def run_research(query: str) -> str:
    """Run the full ARES pipeline: Architect → Specialist → Editor → Notify."""
    if not query.strip():
        return "Please enter a research query."

    agent_input = (
        f"{query}\n\nPlease send the final report to: {DEFAULT_EMAIL}"
    )

    try:
        log.info("Starting research for: %s", query)
        result = await Runner.run(architect_agent, input=agent_input)
        log.info("Research complete. Output length: %d", len(result.final_output))
        return result.final_output
    except Exception as e:
        log.exception("Research pipeline failed")
        return f"**Error:** {type(e).__name__}: {e}"


with gr.Blocks(title="ARES Research System") as demo:
    gr.Markdown(
        "# ARES — Autonomous Research & Extraction System\n"
        "Enter a research query below. The system will plan the research, "
        "search the web, and generate a structured report."
    )

    query_input = gr.Textbox(
        label="Research Query",
        placeholder="e.g. What are the latest breakthroughs in quantum computing?",
    )
    submit_btn = gr.Button("Research", variant="primary")

    gr.Markdown("---")
    output = gr.Markdown(label="Research Report")

    submit_btn.click(fn=run_research, inputs=query_input, outputs=output)
    query_input.submit(fn=run_research, inputs=query_input, outputs=output)

if __name__ == "__main__":
    demo.launch()
