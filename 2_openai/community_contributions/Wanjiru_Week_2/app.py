import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv()

manager = ResearchManager()

async def run(query, answers):
    async for chunk in manager.run(query, answers):
        yield chunk

with gr.Blocks() as ui:
    gr.Markdown("# Deep Research Agent")

    query = gr.Textbox(label="Enter research topic")
    answers = gr.Textbox(label="Clarifications (optional)", lines=5)

    run_btn = gr.Button("Run")
    output = gr.Markdown()

    run_btn.click(run, inputs=[query, answers], outputs=output)

ui.launch()
