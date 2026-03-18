"""Gradio app for the ARES Research System."""

import logging
import gradio as gr
from dotenv import load_dotenv
from agents import Runner, InputGuardrailTripwireTriggered
from ares_agents import architect_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ares-app")
DEFAULT_EMAIL = "gasmyrmougang@gmail.com"

# Map agent to tool names to user-friendly progress messages
AGENT_LABELS = {
    "Research Architect Agent": ("Planning", "Analyzing query and building research strategy..."),
    "Web Specialist Agent": ("Researching", "Searching the web for information..."),
    "Report Editor Agent": ("Writing", "Compiling findings into a structured report..."),
    "Notification Agent": ("Delivering", "Sending report via email..."),
    "Safety Classifier": ("Safety Check", "Validating your query..."),
}

TOOL_LABELS = {
    "Web_Specialist_Agent": ("Researching", "Delegating to Web Specialist..."),
    "Report_Editor_Agent": ("Writing", "Handing off to Report Editor..."),
    "Notification_Agent": ("Delivering", "Handing off to Notification Agent..."),
    "travily_web_search": ("Searching", "Querying Tavily search engine..."),
    "send_email": ("Sending", "Delivering email via Resend..."),
}


def build_status(stage: str, desc: str, steps: list[str]) -> str:
    """Build a live status display with progress log."""
    log_lines = "\n".join(f"- {s}" for s in steps)
    return (
        f"### {stage}\n"
        f"{desc}\n\n"
        f"#### Activity Log\n"
        f"{log_lines}\n"
    )


def handle_agent_event(event, steps: list[str]) -> tuple[str, str] | None:
    """Handle an agent_updated event. Returns (stage, desc) or None."""
    name = event.new_agent.name
    if name not in AGENT_LABELS:
        return None
    stage, desc = AGENT_LABELS[name]
    steps.append(f"**{stage}** — {name} activated")
    return stage, desc


def handle_item_event(event, steps: list[str]) -> tuple[str, str] | None:
    """Handle a run_item event. Returns (stage, desc) or None."""
    if event.name == "tool_called":
        tool_name = event.item.raw_item.name
        if tool_name not in TOOL_LABELS:
            return None
        stage, desc = TOOL_LABELS[tool_name]
        steps.append(f"**{stage}** — calling `{tool_name}`")
        return stage, desc

    if event.name == "tool_output":
        steps.append("✅ Tool completed")

    return None


async def run_research(query: str):
    """Run the full ARES pipeline with real-time streaming progress."""
    if not query.strip():
        yield "Please enter a research query."
        return
    agent_input = f"{query}\n\nPlease send the final report to: {DEFAULT_EMAIL}"
    steps: list[str] = []
    current_stage = "Starting"
    current_desc = "Initializing pipeline..."

    try:
        log.info("Starting research for: %s", query)
        stream = Runner.run_streamed(architect_agent, input=agent_input)
        async for event in stream.stream_events():
            update = None

            if event.type == "agent_updated_stream_event":
                update = handle_agent_event(event, steps)
            elif event.type == "run_item_stream_event":
                update = handle_item_event(event, steps)
            if update:
                current_stage, current_desc = update
            yield build_status(current_stage, current_desc, steps)

        log.info("Research complete. Output length: %d", len(stream.final_output))
        yield stream.final_output

    except InputGuardrailTripwireTriggered as e:
        log.warning("Query blocked by safety guardrail: %s", e)
        yield (
            "### Query Blocked\n\n"
            "Your query was flagged by our safety system and cannot be processed. "
            "Please rephrase with a legitimate research intent."
        )
    except Exception as e:
        log.exception("Research pipeline failed")
        yield f"### Error\n\n**{type(e).__name__}:** {e}"


with gr.Blocks(title="ARES Research System") as demo:
    gr.Markdown(
        "# ARES: Autonomous Research & Extraction System\n"
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
