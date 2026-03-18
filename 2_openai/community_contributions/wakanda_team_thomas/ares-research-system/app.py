"""Gradio app to test the ARES Architect Agent."""

import logging

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ares-app")

log.info("Importing agents...")
from agents import Runner  # noqa: E402
from ares_agents import architect_agent  # noqa: E402
log.info("Imports done.")


async def run_architect(query: str) -> str:
    """Run the Research Architect agent and display the plan."""
    log.info(">>> run_architect called with query: %s", query)

    if not query.strip():
        log.warning("Empty query received")
        return "Please enter a research query."

    try:
        log.info("Starting Runner.run...")
        result = await Runner.run(architect_agent, input=query)
        log.info("Runner.run completed. Output type: %s", type(result.final_output))
        log.info("Output length: %d", len(result.final_output))
        log.info("First 100 chars: %s", result.final_output[:100])
        return result.final_output
    except Exception as e:
        log.exception("Runner.run failed")
        return f"**Error:** {type(e).__name__}: {e}"


with gr.Blocks(title="ARES — Architect Agent Test") as demo:
    gr.Markdown("# ARES — Architect Agent Test")
    gr.Markdown("The Architect plans the research and delegates to the Web Specialist.")

    with gr.Row():
        query_input = gr.Textbox(
            label="Research Query",
            placeholder="e.g. Analyze the impact of AI on healthcare diagnostics",
            scale=4,
        )
        submit_btn = gr.Button("Submit", variant="primary", scale=1)

    output = gr.Markdown(label="Research Results")

    log.info("Binding click event...")
    submit_btn.click(fn=run_architect, inputs=query_input, outputs=output)
    log.info("Binding submit event...")
    query_input.submit(fn=run_architect, inputs=query_input, outputs=output)
    log.info("Events bound.")

if __name__ == "__main__":
    log.info("Launching Gradio app...")
    demo.launch()
