from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

_APP_DIR = Path(__file__).resolve().parent

load_dotenv(_APP_DIR / ".env")
load_dotenv()

_CONTRIB_ROOT = _APP_DIR.parent
if str(_CONTRIB_ROOT) not in sys.path:
    sys.path.insert(0, str(_CONTRIB_ROOT))

import gradio as gr

from job_report.manager import Manager


async def generate_report(job_description: str, company_name: str) -> tuple[str, str | None]:
    manager = Manager()
    markdown_out, pdf_path = await manager.run(job_description, company_name or "")
    return markdown_out, pdf_path


def _ui():
    with gr.Blocks(title="Job interview report") as demo:
        gr.Markdown(
            "# Job interview prep report\n"
            "Paste a **job description**. Optionally add the **company name** to skip inferring it from the text."
        )
        jd = gr.Textbox(
            label="Job description",
            placeholder="Paste the full job posting here…",
            lines=12,
        )
        company = gr.Textbox(
            label="Company name (optional)",
            placeholder="e.g. Acme Corp",
            lines=1,
        )
        btn = gr.Button("Generate report", variant="primary")
        status = gr.Markdown()
        pdf = gr.File(label="Download job_report.pdf")

        btn.click(fn=generate_report, inputs=[jd, company], outputs=[status, pdf])
    return demo


if __name__ == "__main__":
    demo = _ui()
    demo.queue()
    demo.launch()