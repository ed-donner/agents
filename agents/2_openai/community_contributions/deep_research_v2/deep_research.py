import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

research_manager = ResearchManager()

async def run(query: str, clarification: str = None, send_email_flag: bool = False, depth: str = "Standard (10 searches)"):
    async for chunk in research_manager.run(query, clarification, send_email_flag, depth):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    with gr.Row():
        with gr.Column():
            query_textbox = gr.Textbox(label="What topic would you like to research?")
            run_button = gr.Button("Run", variant="primary")

        with gr.Column():
            clarification_textbox = gr.Textbox(label="Clarification (if asked)")

            clarification_button = gr.Button("Submit Clarification", variant="secondary")
    with gr.Row():
        send_email_checkbox = gr.Checkbox(label="Send email with the report", value=True)
    with gr.Row():
        depth_dropdown = gr.Dropdown(
            label="Research depth",
            choices=["Quick Look (5 searches)", "Standard (10 searches)", "In-Depth (20 searches)"],
            value="Standard (10 searches)"
        )

    report = gr.Markdown(label="Report")

    run_button.click(
        fn=run,
        inputs=[query_textbox, clarification_textbox, send_email_checkbox, depth_dropdown],
        outputs=report
    )
    query_textbox.submit(
        fn=run,
        inputs=[query_textbox, clarification_textbox, send_email_checkbox, depth_dropdown],
        outputs=report
    )
    clarification_button.click(
        fn=run,
        inputs=[query_textbox, clarification_textbox, send_email_checkbox, depth_dropdown],
        outputs=report
    )
    clarification_textbox.submit(
        fn=run,
        inputs=[query_textbox, clarification_textbox, send_email_checkbox, depth_dropdown],
        outputs=report
    )

ui.launch(inbrowser=True)
