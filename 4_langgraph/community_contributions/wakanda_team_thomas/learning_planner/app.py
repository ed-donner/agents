"""
Gradio UI for the Learning Path Generator.
Tool testing mode - testing each tool as we build.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)

import gradio as gr
from tools import generate_pdf_from_markdown

print("Starting Learning Planner - Tool Testing...")


def test_pdf_generator(filename: str, content: str) -> str:
    """Test the PDF generator tool."""
    if not filename.strip():
        return "Please enter a filename."
    if not content.strip():
        return "Please enter markdown content."
    result = generate_pdf_from_markdown(content, filename)
    return result


with gr.Blocks(title="Learning Planner - Tool Testing") as ui:
    gr.Markdown("## Tool Testing: PDF Generator")
    gr.Markdown("Convert markdown content to a styled PDF file.")
    
    with gr.Row():
        pdf_name = gr.Textbox(
            label="Filename",
            placeholder="e.g., learning_path (will add .pdf extension)"
        )
    with gr.Row():
        pdf_content = gr.Textbox(
            label="Markdown Content",
            placeholder="# My Learning Path\n\n## Phase 1\n\n- Item 1\n- Item 2",
            lines=12
        )
    with gr.Row():
        pdf_btn = gr.Button("Generate PDF", variant="primary")
    with gr.Row():
        pdf_result = gr.Textbox(label="Result", lines=3)
    
    pdf_btn.click(test_pdf_generator, inputs=[pdf_name, pdf_content], outputs=[pdf_result])


if __name__ == "__main__":
    ui.launch()
