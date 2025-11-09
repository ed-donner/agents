import gradio as gr
from fpdf import FPDF
import tempfile
import re
from orchestrator import run_pipeline

def sanitize_text_for_pdf(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)
def generate_report(topic):
    report_text = run_pipeline(topic)
    sanitized_text = sanitize_text_for_pdf(report_text)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in sanitized_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    temp_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(temp_path)
    return sanitized_text, temp_path

iface = gr.Interface(
    fn=generate_report,
    inputs=gr.Textbox(label="Enter a research topic", placeholder="e.g. Starting Goat Farming in Kenya, Nairobi"),
    outputs=[gr.Textbox(label="Generated Report", lines=20), gr.File(label="Download PDF Report")],
    title=" Research Report Generator",
    description="Enter a topic and get a research, risk, and finance report in PDF form."
)

if __name__ == "__main__":
    iface.launch()
