from __future__ import annotations

import os
import uuid

import gradio as gr

from agent import FiveWhysAgent


async def _setup() -> FiveWhysAgent:
    agent = FiveWhysAgent()
    await agent.setup()
    return agent


async def _free_resources(agent: FiveWhysAgent) -> None:
    if agent is not None:
        await agent.cleanup()


def _new_investigation_id() -> str:
    return f"inv-{uuid.uuid4().hex[:8]}"


async def start_investigation(
    agent: FiveWhysAgent,
    phenomenon: str,
    domain: str,
    equipment_context: str,
    max_depth: int,
    investigation_id: str,
    chatbot: list,
) -> tuple:
    """Start a new investigation and run until the first gemba_check interrupt."""
    if not phenomenon.strip():
        gr.Warning("Please describe the phenomenon before starting.")
        return chatbot, "", "", None, "", agent

    domain_label = domain or "manufacturing"
    chatbot = (chatbot or []) + [
        {
            "role": "user",
            "content": (
                f"**Phenomenon:** {phenomenon}\n\n"
                f"**Domain:** {domain_label}"
                + (f" | **Equipment:** {equipment_context}" if equipment_context else "")
                + f" | **Max depth:** {max_depth} | **ID:** {investigation_id}"
            ),
        },
        {"role": "assistant", "content": "Researching failure modes and generating hypotheses..."},
    ]

    result = await agent.start_investigation(
        phenomenon=phenomenon,
        investigation_id=investigation_id,
        domain=domain_label,
        equipment_context=equipment_context,
        max_depth=max_depth,
    )

    chatbot, hypothesis_text, instructions_text = _update_chat(chatbot, result)
    return chatbot, hypothesis_text, instructions_text, None, "", agent


async def submit_gemba(
    agent: FiveWhysAgent,
    investigation_id: str,
    gemba_result: str,
    gemba_notes: str,
    chatbot: list,
) -> tuple:
    """Submit the operator's Gemba Check result and resume the graph."""
    if not gemba_result:
        gr.Warning("Please select OK, NOK, or Root Cause before submitting.")
        return chatbot, "", "", None, "", agent

    label_map = {
        "OK": "OK — stopped (not a cause)",
        "NOK": "NOK — confirmed cause (go deeper)",
        "ROOT_CAUSE": "ROOT CAUSE — operator confirmed, skip to countermeasure",
    }
    label = label_map.get(gemba_result, f"Result: {gemba_result}")
    chatbot = (chatbot or []) + [
        {"role": "user", "content": f"**Gemba result:** {label}\n\n**Notes:** {gemba_notes or '(none)'}"},
        {"role": "assistant", "content": "Processing result..."},
    ]

    result = await agent.submit_gemba_result(
        investigation_id=investigation_id,
        result=gemba_result,
        notes=gemba_notes,
    )
    chatbot, hypothesis_text, instructions_text = _update_chat(chatbot, result)
    return chatbot, hypothesis_text, instructions_text, None, "", agent


async def export_report(investigation_id: str, agent: FiveWhysAgent) -> tuple[str, str]:
    """Return the markdown report file for download."""
    if not investigation_id.strip():
        gr.Warning("No active investigation to export.")
        return gr.update(), gr.update()

    try:
        nodes = await agent.get_investigation_tree(investigation_id)
        if not nodes:
            gr.Warning("Investigation tree is empty — nothing to export yet.")
            return gr.update(), gr.update()

        report_path = f"investigations/{investigation_id}.md"
        if os.path.exists(report_path):
            return gr.update(value=report_path, visible=True), f"Report ready: {report_path}"
        gr.Warning("Markdown report not found. Complete the investigation first.")
        return gr.update(), gr.update()
    except Exception as e:
        gr.Warning(f"Export failed: {e}")
        return gr.update(), gr.update()


async def reset(agent: FiveWhysAgent) -> tuple:
    """Tear down the current agent and create a fresh one."""
    await agent.cleanup()
    new_agent = FiveWhysAgent()
    await new_agent.setup()
    return (
        new_agent,
        [],
        "",
        "manufacturing",
        "",
        5,
        _new_investigation_id(),
        "",
        "",
        None,
        "",
    )


def _update_chat(chatbot: list, result: dict) -> tuple[list, str, str]:
    """Parse the agent result and append messages to the chatbot history."""
    if chatbot and chatbot[-1]["content"] in (
        "Researching failure modes and generating hypotheses...",
        "Processing result...",
    ):
        chatbot = chatbot[:-1]

    status = result.get("status", "")

    if status == "awaiting_gemba":
        hypothesis = result.get("active_hypothesis", "")
        depth = result.get("depth", 1)
        branch = result.get("branch_path", "")
        instructions = result.get("gemba_instructions", "")
        pending = result.get("pending_count", 0)
        chatbot.append({
            "role": "assistant",
            "content": (
                f"**Gemba Check required** (depth {depth}, branch `{branch}`)\n\n"
                f"**Hypothesis:** {hypothesis}\n\n"
                f"**Instructions:** {instructions}\n\n"
                f"*{pending} more hypothesis/es queued after this one.*"
            ),
        })
        return chatbot, hypothesis, instructions

    if status == "complete":
        nodes = result.get("why_nodes", [])
        report_path = result.get("report_path", "")
        root_causes = [n for n in nodes if n.get("countermeasure")]
        if root_causes:
            rc_summary = "\n".join(
                f"- [{n['branch_path']}] {n['hypothesis']}: **{n['countermeasure']}**"
                for n in root_causes
            )
            chatbot.append({
                "role": "assistant",
                "content": (
                    f"Investigation complete.\n\n**Root causes & countermeasures:**\n{rc_summary}\n\n"
                    + (f"Report saved to `{report_path}`" if report_path else "")
                ),
            })
        else:
            chatbot.append({
                "role": "assistant",
                "content": "Investigation complete. Use 'Export Report' to download the report.",
            })
        return chatbot, "", ""

    return chatbot, "", ""


DOMAINS = [
    "manufacturing",
    "aerospace",
    "automotive",
    "food & beverage",
    "pharmaceuticals",
    "oil & gas",
    "construction",
    "logistics & supply chain",
    "electronics",
    "utilities & energy",
]


with gr.Blocks(title="5 Whys Investigation Agent") as ui:

    agent_state = gr.State(delete_callback=_free_resources)

    gr.Markdown(
        "# 5 Whys Investigation Agent\n"
        "An AI-assisted root cause analysis tool for operational excellence experts."
    )

    with gr.Row():
        # Column 1: Setup
        with gr.Column(scale=1, min_width=260):
            gr.Markdown("### Setup")
            phenomenon_box = gr.Textbox(
                label="Phenomenon (What went wrong?)",
                placeholder="e.g. Glue overflowed from the production tank",
                lines=3,
            )
            domain_dropdown = gr.Dropdown(
                choices=DOMAINS,
                value="manufacturing",
                label="Industry / Domain",
                allow_custom_value=True,
            )
            equipment_box = gr.Textbox(
                label="Equipment / Process Context",
                placeholder="e.g. Hydraulic press line 3 — glue dispensing station",
                lines=2,
            )
            depth_slider = gr.Slider(
                label="Maximum Why Depth", minimum=2, maximum=7, value=5, step=1
            )
            inv_id_box = gr.Textbox(
                label="Investigation ID",
                value=_new_investigation_id(),
                placeholder="Auto-generated — edit if needed",
            )
            start_btn = gr.Button("Start Investigation", variant="primary")

        # Column 2: Investigation Log
        with gr.Column(scale=2, min_width=380):
            gr.Markdown("### Investigation Log")
            chatbot = gr.Chatbot(label="Investigation Log", height=500)

        # Column 3: Gemba Check Input
        with gr.Column(scale=1, min_width=280):
            gr.Markdown("### Gemba Check Input")
            hypothesis_display = gr.Textbox(
                label="Current Hypothesis", interactive=False, lines=2
            )
            instructions_display = gr.Textbox(
                label="What to physically check", interactive=False, lines=4
            )
            gemba_radio = gr.Radio(
                choices=["OK", "NOK", "ROOT_CAUSE"],
                value=None,
                label="Gemba Result",
                info="OK = not a cause (stop) | NOK = confirmed cause (go deeper) | ROOT_CAUSE = skip validator, go straight to countermeasure",
            )
            gemba_notes_box = gr.Textbox(
                label="Gemba Notes (what did you observe?)",
                placeholder="e.g. Level gauge switch found physically stuck. Spring worn out.",
                lines=3,
            )
            submit_gemba_btn = gr.Button("Submit Gemba Result", variant="primary")

    # Bottom row: Export / Reset
    with gr.Row():
        export_md_btn = gr.Button("Export Markdown Report", variant="secondary")
        reset_btn = gr.Button("Reset", variant="stop")
    report_download = gr.File(label="Download Report", visible=False)
    status_msg = gr.Textbox(label="Status", interactive=False, lines=1)

    ui.load(_setup, inputs=[], outputs=[agent_state])

    start_btn.click(
        start_investigation,
        inputs=[agent_state, phenomenon_box, domain_dropdown, equipment_box, depth_slider, inv_id_box, chatbot],
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
    reset_btn.click(
        reset,
        inputs=[agent_state],
        outputs=[
            agent_state, chatbot, phenomenon_box, domain_dropdown, equipment_box,
            depth_slider, inv_id_box,
            hypothesis_display, instructions_display,
            gemba_radio, gemba_notes_box,
        ],
    )


if __name__ == "__main__":
    tui_theme = gr.themes.Monochrome(
        primary_hue="green",
        neutral_hue="neutral",
        radius_size="none",
        spacing_size="sm",
        font=[gr.themes.GoogleFont("JetBrains Mono"), "Courier New", "monospace"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "Courier New", "monospace"],
    )
    ui.launch(inbrowser=True, theme=tui_theme)
