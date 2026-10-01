from pathlib import Path

import gradio as gr
from dotenv import load_dotenv


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV, override=True)

from claim_check_manager import ClaimCheckManager  # noqa: E402


async def check_claim(claim: str, context: str):
    if not claim or len(claim.strip()) < 20:
        yield "Please enter a specific factual claim of at least 20 characters."
        return

    async for update in ClaimCheckManager().run(claim, context):
        yield update


EXAMPLE_CLAIM = "Modern cold-climate heat pumps can remain efficient below freezing."
EXAMPLE_CONTEXT = """Evaluate this for residential heating, including important regional,
building, and equipment limitations. Prefer recent government and research sources."""


with gr.Blocks(title="Claim Check Team") as ui:
    gr.Markdown(
        """# Claim Check Team

Enter a factual claim. The agent team searches for current evidence, challenges the claim,
audits source quality, and returns a cited verdict with calibrated confidence.

*This tool supports research and critical thinking; it is not a substitute for professional advice.*
"""
    )

    claim = gr.Textbox(
        label="Claim to check",
        placeholder="Enter one specific factual claim...",
        lines=3,
    )
    context = gr.Textbox(
        label="Context or scope (optional)",
        placeholder="Add a location, date range, definition, or other useful constraint...",
        lines=5,
    )
    check_button = gr.Button("Check claim", variant="primary")
    output = gr.Markdown()

    gr.Examples(
        examples=[[EXAMPLE_CLAIM, EXAMPLE_CONTEXT]],
        inputs=[claim, context],
    )

    check_button.click(check_claim, inputs=[claim, context], outputs=output)


if __name__ == "__main__":
    ui.launch()
