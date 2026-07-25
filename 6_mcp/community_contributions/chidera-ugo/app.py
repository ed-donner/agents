import gradio as gr
import asyncio
from reviewer import review_code, review_file


def run_review(code: str, file_path: str) -> str:
    if file_path.strip():
        return asyncio.run(review_file(file_path.strip()))
    if code.strip():
        return asyncio.run(review_code(code.strip()))
    return "Paste some code or enter a file path to review."


with gr.Blocks(title="Frontend Code Reviewer", theme=gr.themes.Default(primary_hue="violet")) as ui:
    gr.Markdown("## Frontend Code Reviewer")
    gr.Markdown(
        "Paste a React/TypeScript component below, or enter a file path. "
        "The reviewer checks for accessibility, security, performance, and best practice issues."
    )

    with gr.Row():
        with gr.Column(scale=2):
            code_input = gr.Code(
                label="Paste code here",
                language="typescript",
                lines=25,
            )
            file_input = gr.Textbox(
                label="Or enter a file path or directory",
                placeholder="/path/to/MyComponent.tsx  or  /path/to/src/components",
            )
            review_btn = gr.Button("Review", variant="primary")

        with gr.Column(scale=2):
            output = gr.Markdown(label="Review Report")

    review_btn.click(
        fn=run_review,
        inputs=[code_input, file_input],
        outputs=[output],
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
