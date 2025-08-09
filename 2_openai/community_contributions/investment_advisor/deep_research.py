import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


async def run_with_button_control(query: str):
    """Wrapper function that yields both the content and button state"""
    # First yield: disable button and clear report
    yield "", gr.update(interactive=False)
    
    # Yield each chunk while keeping button disabled
    async for chunk in ResearchManager().run(query):
        yield chunk, gr.update(interactive=False)
    
async def run_with_button_control(query: str):
    """Wrapper function that yields both the content and button state"""
    # First yield: disable button and clear report
    yield "", gr.update(interactive=False)
    
    # Keep track of the last chunk
    last_chunk = ""
    
    # Yield each chunk while keeping button disabled
    async for chunk in ResearchManager().run(query):
        last_chunk = chunk
        yield chunk, gr.update(interactive=False)
    
    # Final yield: re-enable button with the final content
    yield last_chunk, gr.update(interactive=True)


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Your Financial Analyst")
    query_textbox = gr.Textbox(label="What company would you like to know about?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    # Button click event
    run_button.click(
        fn=run_with_button_control, 
        inputs=query_textbox, 
        outputs=[report, run_button]
    )
    
    # Textbox submit event
    query_textbox.submit(
        fn=run_with_button_control, 
        inputs=query_textbox, 
        outputs=[report, run_button]
    )

# For local development
if __name__ == "__main__":
    ui.launch(inbrowser=True)

# For deployment (Gradio will call this automatically)
app = ui

#ui.launch(inbrowser=True)

