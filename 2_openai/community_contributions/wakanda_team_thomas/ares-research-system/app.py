"""Gradio app for the ARES Research System."""

import logging

import gradio as gr
from dotenv import load_dotenv
from agents import Runner, InputGuardrailTripwireTriggered, trace, gen_trace_id
from ares_agents import architect_agent, notification_agent

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
    "Safety Classifier": ("Safety Check", "Validating your query..."),
}

TOOL_LABELS = {
    "Web_Specialist_Agent": ("Researching", "Delegating to Web Specialist..."),
    "Report_Editor_Agent": ("Writing", "Handing off to Report Editor..."),
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
        steps.append("Tool completed")

    return None

async def run_research(query: str):
    """Run the research pipeline with real-time streaming progress."""
    if not query.strip():
        yield {
            output: "Please enter a research query.",
            email_section: gr.update(visible=False),
        }
        return

    steps: list[str] = []
    current_stage = "Starting"
    current_desc = "Initializing pipeline..."

    try:
        trace_id = gen_trace_id()
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        log.info("Starting research for: %s", query)
        log.info("Trace URL: %s", trace_url)

        with trace("ARES Research", trace_id=trace_id):
            stream = Runner.run_streamed(architect_agent, input=query)
            async for event in stream.stream_events():
                update = None
                if event.type == "agent_updated_stream_event":
                    update = handle_agent_event(event, steps)
                elif event.type == "run_item_stream_event":
                    update = handle_item_event(event, steps)
                if update:
                    current_stage, current_desc = update
                yield {
                    output: build_status(current_stage, current_desc, steps),
                    email_section: gr.update(visible=False),
                }

        log.info("Research complete. Output length: %d", len(stream.final_output))
        yield {
            output: stream.final_output,
            email_section: gr.update(visible=True),
        }

    except InputGuardrailTripwireTriggered as e:
        log.warning("Query blocked by safety guardrail: %s", e)
        yield {
            output: (
                "### Query Blocked\n\n"
                "Your query was flagged by our safety system and cannot be processed. "
                "Please rephrase with a legitimate research intent."
            ),
            email_section: gr.update(visible=False),
        }
    except Exception as e:
        log.exception("Research pipeline failed")
        yield {
            output: f"### Error\n\n**{type(e).__name__}:** {e}",
            email_section: gr.update(visible=False),
        }



# Ask for email when the report will be send
async def send_report_email(report: str, email: str):
    """Send the report via the Notification Agent."""
    if not email.strip():
        return gr.update(interactive=True), "Please provide an email address."

    if not report.strip():
        return gr.update(interactive=True), "No report to send. Run a research query first."

    try:
        log.info("Sending report to: %s", email)
        notification_input = (
            f"Send the following report to {email}:\n\n{report}"
        )
        await Runner.run(notification_agent, input=notification_input)
        log.info("Email sent successfully.")
        return gr.update(value="Sent", interactive=False), f"Report sent to **{email}**"
    except Exception as e:
        log.exception("Email delivery failed")
        return gr.update(interactive=True), f"Failed to send: {type(e).__name__}: {e}"


# Gradio App
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
    # Hide until report is ready
    with gr.Group(visible=False) as email_section:
        gr.Markdown("### Send Report via Email")
        email_input = gr.Textbox(
            label="Recipient Email",
            value=DEFAULT_EMAIL,
            type="email",
        )
        send_btn = gr.Button("Send Now", variant="primary")
        email_status = gr.Markdown()

    submit_btn.click(
        fn=run_research,
        inputs=query_input,
        outputs=[output, email_section],
    )
    query_input.submit(
        fn=run_research,
        inputs=query_input,
        outputs=[output, email_section],
    )
    send_btn.click(
        fn=send_report_email,
        inputs=[output, email_input],
        outputs=[send_btn, email_status],
    )

if __name__ == "__main__":
    demo.launch()
