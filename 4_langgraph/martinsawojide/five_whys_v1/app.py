"""
app.py
------
Gradio Blocks UI for the 5 Whys Investigation Agent.

Layout
------
┌─────────────────────────┬──────────────────────────────────────────────┐
│  LEFT — Setup & Input   │  RIGHT — Live Investigation                  │
│  ─────────────────────  │  ─────────────────────────────────────────── │
│  Phenomenon             │  Chatbot (investigation history)             │
│  Domain / Context       │  ─────────────────────────────────────────── │
│  Max Depth slider       │  Gemba Check Panel                          │
│  Investigation ID       │    Hypothesis (read-only)                    │
│  [Start Investigation]  │    Instructions (read-only)                  │
│                         │    OK / NOK radio                            │
│                         │    Notes textbox                             │
│                         │    [Submit Gemba Result]                     │
│                         │  ─────────────────────────────────────────── │
│                         │  [Export Report]  [Reset]                   │
└─────────────────────────┴──────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import uuid

import gradio as gr

from five_whys_agent import FiveWhysAgent

# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------


async def setup() -> FiveWhysAgent:
    agent = FiveWhysAgent()
    await agent.setup()
    return agent


async def free_resources(agent: FiveWhysAgent) -> None:
    if agent is not None:
        await agent.cleanup()


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


def new_investigation_id() -> str:
    return f"inv-{uuid.uuid4().hex[:8]}"


async def start_investigation(
    agent: FiveWhysAgent,
    phenomenon: str,
    domain_context: str,
    max_depth: int,
    investigation_id: str,
    chatbot: list,
) -> tuple:
    """Start a new investigation and run until the first gemba_check interrupt."""
    if not phenomenon.strip():
        gr.Warning("Please describe the phenomenon before starting.")
        return chatbot, "", "", "NOK", "", agent

    chatbot = chatbot or []
    chatbot.append({
        "role": "user",
        "content": f"**Phenomenon:** {phenomenon}\n\n"
                   f"**Domain:** {domain_context or 'not specified'} | "
                   f"**Max depth:** {max_depth} | **ID:** {investigation_id}",
    })
    chatbot.append({
        "role": "assistant",
        "content": "Researching failure modes and generating hypotheses...",
    })

    await agent.setup(
        domain=domain_context.split(".")[0] if domain_context else "manufacturing",
        equipment_context=domain_context,
    )

    result = await agent.start_investigation(
        phenomenon=phenomenon,
        investigation_id=investigation_id,
        max_depth=max_depth,
    )

    chatbot, hypothesis_text, instructions_text = _update_chat_from_result(
        chatbot, result, investigation_id
    )

    return (
        chatbot,
        hypothesis_text,
        instructions_text,
        "NOK",
        "",
        agent,
    )


async def submit_gemba(
    agent: FiveWhysAgent,
    investigation_id: str,
    gemba_result: str,
    gemba_notes: str,
    chatbot: list,
) -> tuple:
    """Submit the operator's Gemba Check result and resume the graph."""
    if not gemba_result:
        gr.Warning("Please select OK or NOK before submitting.")
        return chatbot, "", "", "NOK", "", agent

    result_label = "OK — stopped (not a cause)" if gemba_result == "OK" else "NOK — confirmed cause"
    chatbot = chatbot or []
    chatbot.append({
        "role": "user",
        "content": f"**Gemba result:** {result_label}\n\n**Notes:** {gemba_notes or '(none)'}",
    })
    chatbot.append({
        "role": "assistant",
        "content": "Processing result...",
    })

    result = await agent.submit_gemba_result(
        investigation_id=investigation_id,
        result=gemba_result,
        notes=gemba_notes,
    )

    chatbot, hypothesis_text, instructions_text = _update_chat_from_result(
        chatbot, result, investigation_id
    )

    return (
        chatbot,
        hypothesis_text,
        instructions_text,
        "NOK",
        "",
        agent,
    )


async def export_report(
    investigation_id: str,
    agent: FiveWhysAgent,
) -> tuple[str, str]:
    """Export the markdown investigation report."""
    if not investigation_id.strip():
        gr.Warning("No active investigation to export.")
        return gr.update(), gr.update()

    try:
        nodes = await agent.get_investigation_tree(investigation_id)
        if not nodes:
            gr.Warning("Investigation tree is empty — nothing to export yet.")
            return gr.update(), gr.update()

        import os
        report_path = f"investigations/{investigation_id}.md"
        if os.path.exists(report_path):
            return gr.update(value=report_path, visible=True), f"Markdown report ready: {report_path}"
        gr.Warning("Markdown report not found. Complete the investigation first.")
        return gr.update(), gr.update()
    except Exception as e:
        gr.Warning(f"Export failed: {e}")
        return gr.update(), gr.update()


async def export_8d_pdf(
    investigation_id: str,
    agent: FiveWhysAgent,
) -> tuple[str, str]:
    """Generate and export the AIAG 8D PDF report."""
    if not investigation_id.strip():
        gr.Warning("No active investigation to export.")
        return gr.update(), gr.update()

    try:
        nodes = await agent.get_investigation_tree(investigation_id)
        if not nodes:
            gr.Warning("Investigation tree is empty — start an investigation first.")
            return gr.update(), gr.update()

        pdf_path = await agent.generate_8d_report(investigation_id)
        return gr.update(value=pdf_path, visible=True), f"8D PDF report ready: {pdf_path}"
    except Exception as e:
        gr.Warning(f"8D report generation failed: {e}")
        return gr.update(), gr.update()


async def reset(agent: FiveWhysAgent) -> tuple:
    """Tear down the current agent and create a fresh one."""
    await agent.cleanup()
    new_agent = FiveWhysAgent()
    await new_agent.setup()
    return (
        new_agent,
        [],       # chatbot
        "",       # phenomenon
        "",       # domain_context
        5,        # max_depth
        new_investigation_id(),
        "",       # hypothesis display
        "",       # instructions display
        "NOK",    # gemba radio
        "",       # gemba notes
    )


# ---------------------------------------------------------------------------
# Chat update helper
# ---------------------------------------------------------------------------


def _update_chat_from_result(
    chatbot: list, result: dict, investigation_id: str
) -> tuple[list, str, str]:
    """
    Parse the agent result and append meaningful messages to the chatbot.
    Returns (updated_chatbot, hypothesis_text, instructions_text).
    """
    # Remove the last "Processing..." placeholder
    if chatbot and chatbot[-1]["content"] in (
        "Researching failure modes and generating hypotheses...",
        "Processing result...",
    ):
        chatbot = chatbot[:-1]

    status = result.get("status", "")
    nodes = result.get("why_nodes", [])
    report_path = result.get("report_path", "")
    pending = result.get("pending_count", 0)

    if status == "awaiting_gemba":
        hypothesis = result.get("active_hypothesis", "")
        depth = result.get("depth", 1)
        branch = result.get("branch_path", "")
        instructions = result.get("gemba_instructions", "")

        chatbot.append({
            "role": "assistant",
            "content": (
                f"**Gemba Check required** (branch `{branch}`, depth {depth})\n\n"
                f"**Hypothesis:** {hypothesis}\n\n"
                f"**Instructions:** {instructions}\n\n"
                f"*{pending} more hypothesis/es queued after this one.*"
            ),
        })
        return chatbot, hypothesis, instructions

    elif status == "complete":
        root_causes = [n for n in nodes if n.get("countermeasure")]
        if root_causes:
            rc_summary = "\n".join(
                f"- [{n['branch_path']}] {n['hypothesis']}: **{n['countermeasure']}**"
                for n in root_causes
            )
            chatbot.append({
                "role": "assistant",
                "content": (
                    f"Investigation complete.\n\n"
                    f"**Root causes & countermeasures:**\n{rc_summary}\n\n"
                    + (f"Report saved to `{report_path}`" if report_path else "")
                ),
            })
        else:
            chatbot.append({
                "role": "assistant",
                "content": "Investigation complete. Use 'Export Report' to download the report.",
            })
        return chatbot, "", ""

    # Fallback
    return chatbot, "", ""


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------


with gr.Blocks(
    title="5 Whys Investigation Agent",
    theme=gr.themes.Default(primary_hue="blue"),
) as ui:

    agent_state = gr.State(delete_callback=free_resources)

    gr.Markdown(
        "# 5 Whys Investigation Agent\n"
        "An AI-assisted root cause analysis tool for operational excellence experts."
    )

    with gr.Row():

        # ── Left column — Setup & Input ────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### Setup")

            phenomenon_box = gr.Textbox(
                label="Phenomenon (What went wrong?)",
                placeholder="e.g. Glue overflowed from the production tank",
                lines=3,
            )
            domain_box = gr.Textbox(
                label="Domain / Equipment Context",
                placeholder="e.g. Manufacturing — Hydraulic press line 3",
                lines=2,
            )
            depth_slider = gr.Slider(
                label="Maximum Why Depth",
                minimum=2,
                maximum=7,
                value=5,
                step=1,
            )
            inv_id_box = gr.Textbox(
                label="Investigation ID",
                value=new_investigation_id(),
                placeholder="Auto-generated — edit if needed",
            )
            start_btn = gr.Button("Start Investigation", variant="primary")

        # ── Right column — Live Investigation ──────────────────────────────
        with gr.Column(scale=2):
            gr.Markdown("### Investigation")

            chatbot = gr.Chatbot(
                label="Investigation Log",
                type="messages",
                height=320,
                show_copy_button=True,
            )

            gr.Markdown("#### Gemba Check")

            hypothesis_display = gr.Textbox(
                label="Current Hypothesis",
                interactive=False,
                lines=2,
            )
            instructions_display = gr.Textbox(
                label="What to physically check",
                interactive=False,
                lines=3,
            )

            with gr.Row():
                gemba_radio = gr.Radio(
                    choices=["OK", "NOK"],
                    value="NOK",
                    label="Gemba Result",
                    info="OK = not a cause (stop branch) | NOK = confirmed cause (go deeper)",
                )

            gemba_notes_box = gr.Textbox(
                label="Gemba Notes (what did you observe?)",
                placeholder="e.g. Level gauge switch found physically stuck. Spring worn out.",
                lines=3,
            )

            submit_gemba_btn = gr.Button("Submit Gemba Result", variant="primary")

            with gr.Row():
                export_md_btn = gr.Button("Export Markdown Report", variant="secondary")
                export_8d_btn = gr.Button("Export AIAG 8D Report (PDF)", variant="secondary")
                reset_btn = gr.Button("Reset", variant="stop")

            report_download = gr.File(
                label="Download Report",
                visible=False,
            )
            status_msg = gr.Textbox(label="Status", interactive=False, lines=1)

    # ── Event wiring ───────────────────────────────────────────────────────

    ui.load(setup, inputs=[], outputs=[agent_state])

    start_btn.click(
        start_investigation,
        inputs=[agent_state, phenomenon_box, domain_box, depth_slider, inv_id_box, chatbot],
        outputs=[chatbot, hypothesis_display, instructions_display, gemba_radio, gemba_notes_box, agent_state],
    )

    submit_gemba_btn.click(
        submit_gemba,
        inputs=[agent_state, inv_id_box, gemba_radio, gemba_notes_box, chatbot],
        outputs=[chatbot, hypothesis_display, instructions_display, gemba_radio, gemba_notes_box, agent_state],
    )

    export_md_btn.click(
        export_report,
        inputs=[inv_id_box, agent_state],
        outputs=[report_download, status_msg],
    )

    export_8d_btn.click(
        export_8d_pdf,
        inputs=[inv_id_box, agent_state],
        outputs=[report_download, status_msg],
    )

    reset_btn.click(
        reset,
        inputs=[agent_state],
        outputs=[
            agent_state, chatbot, phenomenon_box, domain_box,
            depth_slider, inv_id_box,
            hypothesis_display, instructions_display,
            gemba_radio, gemba_notes_box,
        ],
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
