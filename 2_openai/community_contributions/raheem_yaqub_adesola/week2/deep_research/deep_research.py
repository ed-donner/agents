
import gradio as gr
from dotenv import load_dotenv
import os
load_dotenv(override=True)
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
print("API KEY:", os.getenv("OPENROUTER_API_KEY"))
from research_manager import ResearchManager

async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks() as ui:
    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(
        label="What topic would you like to research?",
        placeholder="e.g. impact of AI in healthcare"
    )

    run_button = gr.Button("Run")

    report = gr.Markdown()

    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)