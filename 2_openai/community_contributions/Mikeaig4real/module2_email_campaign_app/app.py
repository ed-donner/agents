"""Gradio UI for module 2 email campaign exercise."""

import gradio as gr

from manager import EmailCampaignManager


async def run_campaign(prompt: str):
    """Stream output from the campaign manager."""
    async for chunk in EmailCampaignManager().run(prompt):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Email Campaign App")
    prompt_box = gr.Textbox(
        label="Campaign prompt",
        placeholder="Example: Send a cold email to CTOs about AI-powered SOC2 audit readiness",
    )
    run_button = gr.Button("Generate and dry-run", variant="primary")
    output = gr.Markdown(label="Campaign output")

    run_button.click(fn=run_campaign, inputs=prompt_box, outputs=output)
    prompt_box.submit(fn=run_campaign, inputs=prompt_box, outputs=output)


if __name__ == "__main__":
    ui.launch(inbrowser=True)
