import gradio as gr
from dotenv import (
    find_dotenv,
    load_dotenv,
)

from .agent import generate_responses


load_dotenv(find_dotenv(), override=True)


def main() -> None:
    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown("# Deep Research")
        query_textbox = gr.Textbox(label="What topic would you like to research?")
        run_button = gr.Button("Run", variant="primary")
        report = gr.Markdown(label="Report")

        run_button.click(fn=generate_responses, inputs=query_textbox, outputs=report)  # pylint: disable=no-member
        query_textbox.submit(fn=generate_responses, inputs=query_textbox, outputs=report)  # pylint: disable=no-member

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
