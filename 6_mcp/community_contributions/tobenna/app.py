import asyncio
from typing import Any

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from database import list_leads
from lead_agents import LeadDeskCoordinator

load_dotenv(override=True)

CSS = """
.result-panel {min-height: 220px;}
footer {display: none !important;}
"""


def pipeline_df() -> pd.DataFrame:
    leads = list_leads()
    rows = [
        {
            "Lead ID": lead["id"],
            "Name": lead.get("name", ""),
            "Company": lead.get("company", ""),
            "Status": lead.get("status", ""),
            "Qualification": lead.get("qualification_status", "pending"),
            "Priority": lead.get("priority", "normal"),
            "Owner": lead.get("routing_owner", ""),
            "Queue": lead.get("routing_queue", ""),
            "Notification": lead.get("notification_status", "not_sent"),
            "Summary": lead.get("summary", ""),
        }
        for lead in leads
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "Lead ID",
            "Name",
            "Company",
            "Status",
            "Qualification",
            "Priority",
            "Owner",
            "Queue",
            "Notification",
            "Summary",
        ],
    )


def process_lead(
    freeform_brief: str,
    name: str,
    email: str,
    company: str,
    role_title: str,
    interest: str,
) -> tuple[str, Any]:
    result = asyncio.run(
        LeadDeskCoordinator().process_new_lead(
            freeform_brief,
            name,
            email,
            company,
            role_title,
            interest,
        )
    )
    return result.summary, pipeline_df()


def refresh_pipeline() -> Any:
    return pipeline_df()


with gr.Blocks(title="Lead Intake MCP Orchestration Demo", css=CSS) as demo:
    gr.Markdown(
        "# Lead Intake MCP Orchestration Demo"
    )
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Intake")
            freeform_brief = gr.Textbox(
                label="Lead brief",
                lines=8,
                placeholder="Paste the inbound email, meeting notes, or website inquiry here.",
            )
            name = gr.Textbox(label="Name")
            email = gr.Textbox(label="Email")
            company = gr.Textbox(label="Company")
            role_title = gr.Textbox(label="Role title")
            interest = gr.Textbox(label="Interest / use case")
            submit = gr.Button("Process lead", variant="primary")
            gr.Markdown("The workflow saves the lead, qualifies it, routes it, and conditionally sends a push alert.")
            result = gr.Markdown(elem_classes=["result-panel"])
        with gr.Column(scale=1):
            gr.Markdown("## Saved Leads")
            pipeline = gr.Dataframe(value=pipeline_df(), interactive=False, wrap=True)
            refresh = gr.Button("Refresh leads")

    submit.click(
        fn=process_lead,
        inputs=[freeform_brief, name, email, company, role_title, interest],
        outputs=[result, pipeline],
    )
    refresh.click(fn=refresh_pipeline, outputs=[pipeline])


if __name__ == "__main__":
    demo.launch(inbrowser=True)