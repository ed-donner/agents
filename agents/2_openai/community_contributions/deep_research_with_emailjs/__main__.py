import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

async def run(query: str, email: str, report: str):
    async for chunk in ResearchManager().run(query, email):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    with gr.Row(scale=5):
        with gr.Column(scale=3):
            query_textbox = gr.Textbox(label="What topic would you like to research?")

        with gr.Column(scale=2):
            email_txt = gr.Textbox(label="Want a copy of this report? Just drop your email.", placeholder="you@example.com", scale=4)

    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")

    run_button.click(fn=run, inputs=[query_textbox, email_txt, report], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, email_txt, report], outputs=report)
    email_txt.submit(fn=run, inputs=[query_textbox, email_txt, report], outputs=report)

ui.launch()
