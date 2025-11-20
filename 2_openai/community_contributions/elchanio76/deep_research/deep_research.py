import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

# Create a shared instance to persist the report
research_manager = ResearchManager()

async def run(query: str):
    async for chunk in research_manager.run(query):
        yield chunk

async def chat(message: str, history: list[tuple[str, str]]):
    async for chunk in research_manager.chat(message, history):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

    # Add Q&A Chat section
    gr.Markdown("## Q&A")
    chatbot = gr.ChatInterface(fn=chat)

ui.launch(inbrowser=True)

