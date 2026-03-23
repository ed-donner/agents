"""
Gradio UI for the Learning Path Generator.
Tool testing mode - testing each tool as we build.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)

import gradio as gr
from tools import send_email_with_pdf, create_email_body, SANDBOX_DIR

print("Starting Learning Planner - Tool Testing...")


def test_email_notifier(to_email: str, topic: str, pdf_filename: str) -> str:
    """Test the email notifier tool."""
    if not to_email.strip():
        return "Please enter an email address."
    if not topic.strip():
        return "Please enter a topic."
    if not pdf_filename.strip():
        return "Please enter a PDF filename."
    
    if not pdf_filename.endswith(".pdf"):
        pdf_filename = f"{pdf_filename}.pdf"
    
    pdf_path = SANDBOX_DIR / pdf_filename
    
    if not pdf_path.exists():
        return f"Error: PDF file not found at {pdf_path}. Generate a PDF first."
    
    email_body = create_email_body(topic, total_phases=5, total_days=14)
    subject = f"Your Learning Path for {topic} is Ready!"
    
    result = send_email_with_pdf(
        to_email=to_email,
        subject=subject,
        body_html=email_body,
        pdf_path=str(pdf_path),
    )
    return result


def list_available_pdfs() -> str:
    """List PDF files in the sandbox directory."""
    SANDBOX_DIR.mkdir(exist_ok=True)
    pdfs = list(SANDBOX_DIR.glob("*.pdf"))
    if not pdfs:
        return "No PDF files found. Generate a PDF first using the PDF Generator."
    return "\n".join([f"- {p.name}" for p in pdfs])


with gr.Blocks(title="Learning Planner - Tool Testing") as ui:
    gr.Markdown("## Tool Testing: Email Notifier (Resend)")
    gr.Markdown("Send a learning path PDF to an email address.")
    
    with gr.Row():
        available_pdfs = gr.Textbox(
            label="Available PDFs in sandbox",
            value=list_available_pdfs(),
            interactive=False,
            lines=3
        )
    
    with gr.Row():
        email_input = gr.Textbox(
            label="Recipient Email",
            placeholder="e.g., user@example.com"
        )
    with gr.Row():
        topic_input = gr.Textbox(
            label="Topic",
            placeholder="e.g., Kubernetes, LangGraph"
        )
    with gr.Row():
        pdf_input = gr.Textbox(
            label="PDF Filename",
            placeholder="e.g., learning_path (from sandbox directory)"
        )
    with gr.Row():
        send_btn = gr.Button("Send Email", variant="primary")
        refresh_btn = gr.Button("Refresh PDF List")
    with gr.Row():
        email_result = gr.Textbox(label="Result", lines=3)
    
    send_btn.click(
        test_email_notifier,
        inputs=[email_input, topic_input, pdf_input],
        outputs=[email_result]
    )
    refresh_btn.click(list_available_pdfs, outputs=[available_pdfs])


if __name__ == "__main__":
    ui.launch()
