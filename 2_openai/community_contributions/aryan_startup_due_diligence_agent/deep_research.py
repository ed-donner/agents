import os
from dotenv import load_dotenv
load_dotenv(override=True)

import gradio as gr
from research_manager import ResearchManager


async def run(query: str, recipient_email: str):
    async for chunk in ResearchManager().run(query, recipient_email):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Startup Due Diligence")
    query_textbox = gr.Textbox(label="What idea would you like to research?")
    recipient_email_textbox = gr.Textbox(label="Recipient Email Address")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=[query_textbox, recipient_email_textbox], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, recipient_email_textbox], outputs=report)

ui.launch(inbrowser=True)


