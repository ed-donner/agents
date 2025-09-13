import gradio as gr
from dotenv import load_dotenv
from research_controller import ResearchController

load_dotenv(override=True)

print("Loading environment variables...")

async def run(query: str):
    print(f"Running research for query: {query}")
    yield "Please wait...."
    async for chunk in ResearchController().run_research_agent(query):
        yield chunk

print("Creating Gradio interface...")

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    with gr.Row():
        run_button = gr.Button("Run", variant="primary")
        clear_button = gr.Button("Clear", variant="secondary")

    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    clear_button.click(fn=lambda: ("", ""), inputs=None, outputs=[query_textbox, report])

    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

print("Launching Gradio interface...")
ui.launch(inbrowser=True)

print("Gradio interface closed.")