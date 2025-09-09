import gradio as gr
from dotenv import load_dotenv, find_dotenv

env_path = find_dotenv()
load_dotenv(dotenv_path=env_path, override=True)

from research_manager import ResearchManager


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    ui.queue(default_concurrency_limit=5)
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?", value="Latest agentic AI frameworks in 2025")
    run_button = gr.Button("Run", variant="primary")
    notifications = gr.Textbox(label="Notifications", lines=1, interactive=True)
    report = gr.HTML(label="Report")
    run_button.click(fn=run, inputs=query_textbox, outputs=[notifications, report])
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=[notifications, report])
ui.launch(inbrowser=True)
