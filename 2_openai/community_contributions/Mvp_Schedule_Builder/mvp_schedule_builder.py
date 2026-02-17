import gradio as gr
from dotenv import load_dotenv

from product_planner import ProductPlanner
from tools.calendar_integration import GoogleCalendarIntegration

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ProductPlanner().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Product Planner")
    query_textbox = gr.Textbox(
        label="What is your idea for a new product? Lets make a plan to build it."
    )
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")

    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)
