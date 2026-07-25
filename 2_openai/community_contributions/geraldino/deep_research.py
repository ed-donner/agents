import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# 🔬 Enhanced Deep Research")
    gr.Markdown(
        "Powered by: **Query Refiner** (Gemini) → **Validator Loop** (DeepSeek) → "
        "**Search** (GPT-4o-mini) → **Writer** (GPT-4o-mini) → **Evaluator** (GPT-4o)"
    )
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")

    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)
