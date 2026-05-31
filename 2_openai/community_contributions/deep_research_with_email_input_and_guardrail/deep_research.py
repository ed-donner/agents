import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str, email_to=None):
    # Use async for (iterator) combined with yield at the other end to see the progress
    async for chunk in ResearchManager().run(query, email_to):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown("#### The research report will be output at the bottom of markdown area.")
    with gr.Row(scale=5):
        with gr.Column(scale=3):
            query_textbox = gr.Textbox(label="What topic would you like to research?")

        with gr.Column(scale=2):
            email_textbox = gr.Textbox(label="Want a copy of this report? Leave your email.", placeholder="you@example.com", scale=4)

    run_button = gr.Button("Submit", variant="primary")
    report = gr.Markdown(label="Report")
    run_button.click(fn=run, inputs=[query_textbox, email_textbox], outputs=report)

ui.launch(inbrowser=True)

